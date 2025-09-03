# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Red Hat, Inc.
import os
import sys
from typing import List
from ssg.profiles import _load_yaml_profile_file, get_profiles_from_products

import logging

"""
Description:
    This module is designed to get all the available controls for each product.

    It is particularly useful to determine which controls will impact the product.
    We could according to the available controls to update
    the related OSCAL profiles.

    The output is a set of controls,
    How to run it:
    python get_product_controls.py '<product>' '<content_root_dir>'"
    E.g., $python get_product_controls.py "rhel8" "/path/of/cac-content"
Output Format:
    The module produces an output dictionary with the following structure:

   {'pcidss_4', 'anssi', 'cis_rhel8'}
"""

logging.basicConfig(level=logging.INFO, format="%(message)s")


def get_profile_controls(cac_profile) -> List:
    """Get the policy and levels"""
    profile_yaml = _load_yaml_profile_file(cac_profile)
    policy_ids = []
    # Get the selections from the profile
    selections = profile_yaml.get("selections", [])
    # Process each selected policy
    for selected in selections:
        # Split the selected item into parts based on ":"
        if ":" in selected:
            parts = selected.split(":")
            policy_id = parts[0]  # The policy ID is the first part
            if policy_id is not None:
                policy_ids.append(policy_id)
    return policy_ids


def main(product, content_root_dir):
    profiles = get_profiles_from_products(content_root_dir, [f"{product}"], sorted=True)
    policy_ids = []
    for profile in profiles:
        profile_name = profile.profile_id + ".profile"
        cac_profile = os.path.join(
            content_root_dir,
            "products",
            product,
            "profiles",
            profile_name
        )
        policy_id = get_profile_controls(cac_profile)
        policy_ids.extend(policy_id)
    policy_ids = set(policy_ids)
    # The srg_gpos can't work. It will impact the CI sync-cac-oscal.
    # https://github.com/ComplianceAsCode/content/actions/runs/17401140387/job/49394339232
    # Remove it from the controls to skip do the sync of srg_gpos
    if product == "rhel10":
        policy_ids.discard("srg_gpos")
    logging.info(" ".join(policy_ids))


if __name__ == "__main__":
    # Ensure that the script is run with the correct number of arguments
    if len(sys.argv) != 3:
        logging.warning("Usage: \
            python get_product_controls.py '<product>' '<content_root_dir>'")
        sys.exit(1)
    try:
        # Extract arguments
        product = sys.argv[1]  # First argument is product
        content_root_dir = sys.argv[2]  # Second argument is content_root_dir
        # Call the main function
        main(product, content_root_dir)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
