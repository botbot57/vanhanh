from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import json

def get_esxi_info(vcenter_host, vcenter_user, vcenter_password, esxi_host):
    # Bỏ qua chứng chỉ SSL
    context = ssl._create_unverified_context()

    # Kết nối đến vCenter
    si = SmartConnect(host=vcenter_host, user=vcenter_user, pwd=vcenter_password, sslContext=context)
    content = si.RetrieveContent()

    # Duyệt qua các host để tìm host cụ thể
    result = {}
    for datacenter in content.rootFolder.childEntity:
        for cluster in datacenter.hostFolder.childEntity:
            for host in cluster.host:
                if host.name == esxi_host:
                    summary = host.summary
                    # Lấy thông tin datastore
                    datastores = []
                    for ds in host.datastore:
                        ds_info = ds.summary
                        capacity_gb = ds_info.capacity / (1024 ** 3)
                        free_space_gb = ds_info.freeSpace / (1024 ** 3)
                        used_space_gb = (ds_info.capacity - ds_info.freeSpace) / (1024 ** 3)
                        provisioned_space_gb = used_space_gb  # Mặc định bằng used_space_gb
                        if ds_info.uncommitted is not None:
                            provisioned_space_gb += ds_info.uncommitted / (1024 ** 3)

                        datastores.append({
                            "name": ds_info.name,
                            "capacity_gb": round(capacity_gb, 2),
                            "free_space_gb": round(free_space_gb, 2),
                            "used_space_gb": round(used_space_gb, 2),
                            "provisioned_space_gb": round(provisioned_space_gb, 2)
                        })

                    # Sắp xếp datastore theo free_space_gb giảm dần
                    datastores.sort(key=lambda x: x["free_space_gb"], reverse=True)

                    # Kết quả trả về
                    result = {
                        "esxi_host": host.name,
                        "cpu_usage_percent": round((summary.quickStats.overallCpuUsage / (summary.hardware.cpuMhz * summary.hardware.numCpuCores)) * 100, 2),
                        "memory_usage_percent": round(((summary.quickStats.overallMemoryUsage * 1024 * 1024) / host.hardware.memorySize) * 100, 2),
                        "datastores": datastores
                    }
    
    # Ngắt kết nối vCenter
    Disconnect(si)
    return result

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--vcenter_host", required=True, help="vCenter server hostname or IP")
    parser.add_argument("--vcenter_user", required=True, help="vCenter username")
    parser.add_argument("--vcenter_password", required=True, help="vCenter password")
    parser.add_argument("--esxi_host", required=True, help="ESXi hostname")

    args = parser.parse_args()

    data = get_esxi_info(args.vcenter_host, args.vcenter_user, args.vcenter_password, args.esxi_host)
    print(json.dumps(data, indent=4))
