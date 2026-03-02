import pytest

from src.allocator.engine import HypervisorAllocator, InsufficientResourcesError


class TestAllocator:
    """
    Test deprovisioning -- Deprovision happycase, Deprovision nonexistent throws, Deprovision twice throws on second
    Test provision + deprovision + provision succeeds
    Test provision existing droplet throws

    """

    HOST1 = "host1"
    HOST2 = "host2"
    HOST3 = "host3"

    DROPLET1 = "droplet1"
    DROPLET2 = "droplet2"
    DROPLET3 = "droplet3"
    DROPLET4 = "droplet4"

    @pytest.fixture()
    def allocator(self):
        hosts = [
            {"id": self.HOST1, "cpu_available": 16, "ram_available": 16},
            {"id": self.HOST2, "cpu_available": 12, "ram_available": 12},
            {"id": self.HOST3, "cpu_available": 32, "ram_available": 24},
        ]

        return HypervisorAllocator(hosts)

    def test_single_provision_happyCase_succeeds(self, allocator):
        vm = (self.DROPLET1, 4, 4)  # 4 gb cpu/ram required
        host = allocator.provision(*vm)

        assert host == self.HOST2

    def test_single_provision_too_large_throws(self, allocator):
        vm = (self.DROPLET1, 100, 100)  # 4 gb cpu/ram required

        with pytest.raises(InsufficientResourcesError):
            allocator.provision(*vm)

    def test_multiple_provision_exact_cpu_happyCase_succeeds(self, allocator):
        vm1 = (self.DROPLET1, 4, 4)
        vm2 = (self.DROPLET2, 2, 6)
        vm3 = (self.DROPLET3, 6, 2)

        host1 = allocator.provision(*vm1)
        host2 = allocator.provision(*vm2)
        host3 = allocator.provision(*vm3)

        assert host1 == self.HOST2
        assert host2 == self.HOST2
        assert host3 == self.HOST2

    def test_multiple_provisions_too_large_throws(self, allocator):
        vm1 = (self.DROPLET1, 12, 12)
        vm2 = (self.DROPLET2, 16, 16)
        vm3 = (self.DROPLET3, 24, 24)
        vm4 = (self.DROPLET4, 8, 8)

        selected_host1 = allocator.provision(*vm1)
        selected_host2 = allocator.provision(*vm2)
        selected_host3 = allocator.provision(*vm3)

        assert selected_host1 == self.HOST2
        assert selected_host2 == self.HOST1
        assert selected_host3 == self.HOST3

        with pytest.raises(InsufficientResourcesError):
            allocator.provision(*vm4)
