def jobsMapping = [
  tags: [jobName:"App GWAPortal", jobTags: "reload", extraVars: "app_generic_image_tag: latest"]
]

buildDockerImage([
    imageName: "gwaportal-gwas-server",
    pushRegistryNamespace: "nordborglab/gwaportal",
    pushBranches: ['develop', 'master'],
    tower: jobsMapping
])