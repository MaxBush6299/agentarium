targetScope = 'resourceGroup'

param location string = resourceGroup().location

output deploymentComplete string = 'Success'
