from dataclasses import dataclass, field


@dataclass
class VirtualMachine:
    id: str
    cpu_required: float
    ram_required: float
    assigned_host_id: str = None


@dataclass
class Host:
    id: str
    cpu_available: float
    ram_available: float
    allocated_vms: dict[str, VirtualMachine] = field(default_factory=dict)

    @property
    def ram_remaining(self):
        return self.ram_available - sum(
            vm.ram_required for vm in self.allocated_vms.values()
        )

    @property
    def cpu_remaining(self):
        return self.cpu_available - sum(
            vm.cpu_required for vm in self.allocated_vms.values()
        )


class AllocatorError(RuntimeError):
    pass


class InsufficientResourcesError(AllocatorError):
    pass


class DropletAlreadyProvisioned(AllocatorError):
    pass


class UnknownDropletIDError(AllocatorError):
    pass


class HypervisorAllocator:
    def __init__(self, hosts_json: list[dict]):
        hosts = [
            Host(
                id=host["id"],
                cpu_available=host["cpu_available"],
                ram_available=host["ram_available"],
            )
            for host in hosts_json
        ]
        self.hosts = {host.id: host for host in hosts}
        self.droplets = dict()  # vm id -> VM
        self.anti_affinity_groups = dict()  # group name -> host id

    def provision(
        self,
        droplet_id: str,
        cpu_req: float,
        ram_req: float,
        anti_affinity_group: str = None,
    ) -> str:
        if droplet_id in self.droplets:
            raise DropletAlreadyProvisioned

        selected_host = None
        min_overhead = float("inf")

        for host in self.hosts.values():
            if (
                anti_affinity_group is not None
                and host.id in self.anti_affinity_groups.get(anti_affinity_group, [])
            ):
                continue
            if cpu_req <= host.cpu_remaining and ram_req <= host.ram_remaining:
                overhead = host.cpu_remaining - cpu_req + host.ram_remaining - ram_req
                if overhead < min_overhead:
                    min_overhead = overhead
                    selected_host = host.id

        if selected_host is None:
            raise InsufficientResourcesError

        vm = VirtualMachine(
            droplet_id, cpu_req, ram_req, assigned_host_id=selected_host
        )
        if anti_affinity_group is not None:
            if anti_affinity_group not in self.anti_affinity_groups:
                self.anti_affinity_groups[anti_affinity_group] = []
            self.anti_affinity_groups[anti_affinity_group].append(selected_host)

        self.droplets[droplet_id] = vm
        self.hosts[selected_host].allocated_vms[droplet_id] = vm

        return selected_host

    def deprovision(self, droplet_id: str):
        if droplet_id not in self.droplets:
            raise UnknownDropletIDError

        vm = self.droplets[droplet_id]
        del self.hosts[vm.assigned_host_id].allocated_vms[vm.id]
        del self.droplets[droplet_id]

    def stats(self) -> tuple[float, float]:
        # cpu, ram
        total_cpu_available = sum(host.cpu_available for host in self.hosts.values())
        total_ram_available = sum(host.ram_available for host in self.hosts.values())
        total_cpu_used = sum(vm.cpu_required for vm in self.droplets.values())
        total_ram_used = sum(vm.ram_required for vm in self.droplets.values())

        return (
            total_cpu_used / total_cpu_available,
            total_ram_used / total_ram_available,
        )