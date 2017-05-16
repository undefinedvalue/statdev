#!/usr/bin/env python

# Invalidates CDNs so the caches are refreshed

import boto3
import os
import time

def build(src_dir, dst_dir, opts):
  distribution_id = os.environ['CF_DIST_ID']

  cf = boto3.client('cloudfront')
  cf.create_invalidation(DistributionId=distribution_id,
                                InvalidationBatch={
                                  'Paths': { 'Quantity': 1, 'Items': ['/*'] },
                                  'CallerReference': str(time.time())
                                })

