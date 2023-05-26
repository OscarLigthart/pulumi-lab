"""A Google Cloud Python Pulumi program"""

import pulumi
import pulumi_gcp as gcp
import pulumi_docker as docker
from pulumi_gcp import storage, cloudrun

# Import the program's configuration settings.
config = pulumi.Config()
site_path = config.get("site")
project = config.get("project")
location = config.get("location")

# Create a GCP resource (Storage Bucket)
bucket = storage.Bucket('app-bucket', location=location)

# create bucket object for site
site = gcp.storage.BucketObject("site",
    bucket=bucket.name,
    name="index.html",
    source=pulumi.FileAsset(site_path)
)

# Create a container image for the service.
image = docker.Image(
    "image",
    image_name=f"gcr.io/{project}/site",
    build=docker.DockerBuildArgs(
        context="../app",
        platform="linux/amd64"
    ),
)

# Create a Cloud Run service definition.
service = cloudrun.Service(
    "service",
    cloudrun.ServiceArgs(
        location=location,
        name="demo-app",
        template=cloudrun.ServiceTemplateArgs(
            spec=cloudrun.ServiceTemplateSpecArgs(
                containers=[
                    cloudrun.ServiceTemplateSpecContainerArgs(
                        image=image.image_name,
                        resources=cloudrun.ServiceTemplateSpecContainerResourcesArgs(
                            limits=dict(
                                memory="1Gi",
                                cpu="1",
                            ),
                        ),
                        ports=[
                            cloudrun.ServiceTemplateSpecContainerPortArgs(
                                container_port="8080",
                            ),
                        ],
                        envs=[
                            cloudrun.ServiceTemplateSpecContainerEnvArgs(
                                name="FLASK_RUN_PORT",
                                value="8080",
                            ),
                            cloudrun.ServiceTemplateSpecContainerEnvArgs(
                                name="CLOUD_STORAGE_BUCKET",
                                value=bucket.name,
                            ),
                        ],
                    ),
                ],
                container_concurrency="50",
            ),
        ),
    ),
)

# Create an IAM member to make the service publicly accessible.
invoker = cloudrun.IamMember(
    "invoker",
    cloudrun.IamMemberArgs(
        location=location,
        service=service.name,
        role="roles/run.invoker",
        member="allUsers",
    ),
)

# Export the DNS name of the bucket
pulumi.export('bucket_name', bucket.url)
