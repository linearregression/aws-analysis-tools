#!/usr/bin/env python
#
# updates instance tag in ec2, with puppet classes
# run from each instance, periodically.
#
# Requires:
# * You dump all facts from puppet to a .yaml file, so we can read applied classes
#   See: http://www.semicomplete.com/blog/geekery/puppet-facts-into-mcollective.html
# * Instance metadata service is enabled
#
# Caveat: EC2 only allows 255 chars for the value. You must limit the number of
# classes you shove in the 'puppet_classes' key. See the two vars below the imports.
import boto.ec2
import sys
import collections
import yaml

ec2_tag_key = 's_classes'
ec2_tag_val_startswith = 's_'  # the classes we care about start with s_*
facts_yaml = '/mnt/tmp/facts.yaml'


def get_current_region():
    """
    Query the instance metadata service and return the region this instance is
    placed in.
     """
    return boto.utils.get_instance_metadata()['placement']['availability-zone'].strip().lower()[:-1]


if __name__ == '__main__':
    with open(facts_yaml) as fh:
        puppet = yaml.safe_load(fh)

    regions = boto.ec2.regions()

    region = [region for region in regions if get_current_region() in region.name][0]

    ec2 = region.connect()

    res = ec2.get_all_instances(filters={'instance-id': puppet.get('instance_id')})[0]
    instance = res.instances[0]

    #print instance.tags.get('Name'), instance.id, instance.placement

    s_classes = ','.join([str(classes) for classes in puppet['krux_classes'].split()
                          if classes.startswith(ec2_tag_val_startswith)])

    ec2.create_tags([instance.id], {ec2_tag_key: s_classes})