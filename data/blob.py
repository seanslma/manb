# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: p12
#     language: python
#     name: python3
# ---

# +
import numpy as np
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobLeaseClient, BlobPrefix

account_name = 'my-account-name'
container_name = 'my-container-name'


# +
def get_blob_container_client(
    account_name: str,
    container_name: str,
) -> ContainerClient:
    # Create the BlobServiceClient object
    # blob_service_client = BlobServiceClient(account_url, credential=credential)
    # container_client = blob_service_client.get_container_client(container=container_name)
    container_client = ContainerClient(
        account_url=f'https://{account_name}.blob.core.windows.net',
        credential=DefaultAzureCredential(),
        container_name=container_name,
    )
    return container_client

def get_blobs(
    container_client: ContainerClient,
    blob_prefix: str = '',
) -> list[str]:
    blob_names = [
        blob.name
        for blob in container_client.walk_blobs(name_starts_with=blob_prefix, delimiter='/')
        if not isinstance(blob, BlobPrefix)
    ]
    return blob_names

def blobs_size_mb(
    container_client: ContainerClient,
    blob_prefix: str = '',
) -> list[str]:
    blob_sizes = [
        blob.size
        for blob in container_client.walk_blobs(name_starts_with=blob_prefix, delimiter='/')
        if not isinstance(blob, BlobPrefix)
    ]
    return np.sum(np.array(blob_sizes)) / 1024 / 1024

def move_blob(
    container_client: ContainerClient,
    source_blob_fullpath: str,
    dest_blob_path: str,
):
    """
    Move blob file to another folder in the same blob container
    """
    # Make sure source blob exists
    source_blob = container_client.get_blob_client(blob=source_blob_fullpath)
    if source_blob.exists():
        # # Lease source blob during copy to prevent other clients from modifying it
        # lease = BlobLeaseClient(client=source_blob)
        # lease.acquire(-1) # Create an infinite lease

        # Get source blob properties
        source_blob_properties = source_blob.get_blob_properties()

        # Copy blob
        blob_filename = source_blob_fullpath.rsplit('/', 1)[-1]
        dest_blob = container_client.get_blob_client(blob=f'{dest_blob_path}/{blob_filename}')
        dest_blob.start_copy_from_url(source_url=source_blob.url)

        dest_blob_properties = dest_blob.get_blob_properties()
        dest_blob_properties.creation_time = source_blob_properties.creation_time
        dest_blob_properties.last_modified = source_blob_properties.last_modified
        dest_blob.set_blob_properties(blob_properties=dest_blob_properties)

        # # Break source blob lease
        # if source_blob_properties.lease.state == "leased":
        #     lease.break_lease()

        # Delete source blob
        #source_blob.delete_blob()

        return source_blob_properties


# -

container_client = get_blob_container_client(account_name, container_name)
blob_list = get_blobs(container_client, blob_prefix='data/sales/2022/01/08/3120267066/')
for blob in blob_list:
    print(blob)
    move_blob(container_client, blob, 'data/sales/2022/01')

container_client = get_blob_container_client(account_name, container_name)
blob_size = blobs_size_mb(container_client, blob_prefix='data/sales/2023/05/30/')
print(f'total size: {blob_size:.3f} MB')

blob = 'test-20230428000008.csv'
p0 = move_blob(container_client, blob, 'manage')
p0

blob = '2021/07/test-20210706000012.parquet'
blob_client = container_client.get_blob_client(blob=blob)
po = blob_client.get_blob_properties()
po

blob = '2021/test-20210706000012.parquet'
blob_client = container_client.get_blob_client(blob=blob)
pn = blob_client.get_blob_properties()
pn

blob = 'test-20230427000004.parquet'
blob_client = container_client.get_blob_client(blob=blob)
px = blob_client.get_blob_properties()
px
