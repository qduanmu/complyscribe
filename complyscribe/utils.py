# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Common utility functions."""
import os
import pathlib
import textwrap
from typing import Any, List, Optional, Tuple

from ruamel.yaml import YAML, CommentedMap, CommentToken
from ruamel.yaml.scalarstring import LiteralScalarString
from ssg.controls import ControlsManager, Policy
from ssg.products import load_product_yaml, product_yaml_path
from trestle.common.const import MODEL_TYPE_PROFILE
from trestle.common.model_utils import ModelUtils
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal.profile import Profile

from complyscribe.tasks.authored.profile import CatalogControlResolver


def populate_if_dict_field_not_exist(
    data: CommentedMap, field_name: str, default_value: Any
) -> Any:
    """
    Set field with default value if a CommentedMap field does not exist,
    if filed exists, this is a no-op
    return field value
    """
    if data.get(field_name) is None:
        # insert new filed to -2 position, avoid extra newline
        data.insert(len(data) - 1, field_name, default_value)

    return data[field_name]


def get_comments_from_yaml_data(yaml_data: Any) -> List[str]:
    """
    Get all comments from yaml_data, yaml_data must be read
    using ruamel.yaml library
    """
    comments: List[str] = []
    if not yaml_data.ca.items:
        return comments

    for _, comment_info in yaml_data.ca.items.items():
        for comment in comment_info:
            if not comment:
                continue

            if isinstance(comment, List):
                for c in comment:
                    if isinstance(c, CommentToken):
                        comments.append(c.value)
            elif isinstance(comment, CommentToken):
                comments.append(comment.value)

    return comments


def get_field_comment(data: CommentedMap, field_name: str) -> List[str]:
    """
    Get comments under specific field from data, data must be read
    using ruamel.yaml library
    """
    result = []
    comments = data.ca.items.get(field_name, [])

    for comment in comments:
        if not comment:
            continue

        if isinstance(comment, List):
            for c in comment:
                if isinstance(c, CommentToken):
                    result.append(c.value)
        elif isinstance(comment, CommentToken):
            result.append(comment.value)

    return result


def read_cac_yaml_ordered(file_path: pathlib.Path) -> Any:
    """
    Read data from CaC content yaml file while preserving the order
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    return yaml.load(file_path)


def write_cac_yaml_ordered(file_path: pathlib.Path, data: Any) -> None:
    """
    Serializes a Python object into a CaC content YAML stream, preserving the order.
    """
    yaml = YAML()
    # align with CaC content yaml file style
    yaml.indent(mapping=4, sequence=6, offset=4)
    yaml.explicit_start = True
    # temp workaround to mitigate line length difference
    # between CaC yamlfix and complyscribe ruamel.yaml
    yaml.width = 110
    yaml.dump(data, file_path)


def load_controls_manager(cac_content_root: str, product: str) -> ControlsManager:
    """
    Loads and initializes a ControlsManager instance.
    """
    product_yml_path = product_yaml_path(cac_content_root, product)
    product_yaml = load_product_yaml(product_yml_path)
    product_yaml = product_yaml._data_as_dict
    controls_dir = os.path.join(cac_content_root, "controls")
    control_mgr = ControlsManager(controls_dir, product_yaml)
    control_mgr.load()
    return control_mgr


def load_cac_policy(
    policy_file_path: pathlib.Path, product: Optional[str] = None
) -> Policy:
    """
    Load CaC content policy from YAML file.
    """

    if product is None:
        # use a fake product_dir if we do not know the product. It's ok to do this when using
        # ssg as a third-party library. Because in ssg, only use product_dir parent dir to find
        # jinja macros directory
        # https://github.com/ComplianceAsCode/content/blob/master/ssg/jinja.py#L101-L105
        product_dir = policy_file_path
    else:
        product_dir = policy_file_path.parent.parent.parent.joinpath(
            "products", product
        )
    # add product_dir to env_yaml to avoid get incorrect jinja macros directory
    policy = Policy(policy_file_path, env_yaml={"product_dir": product_dir})
    policy.load()

    return policy


def to_literal_scalar_string(s: str) -> LiteralScalarString:
    """
    Convert a string to a literal scalar string.
    """
    return LiteralScalarString(textwrap.dedent(s))


def get_oscal_profiles(
    trestle_root: pathlib.Path, product: str, cac_policy_id: str
) -> List[Tuple[Profile, pathlib.Path]]:
    """
    Get OSCAL profiles information according to product name
     and CaC policy id.
    """
    res = []
    dir_name = ModelUtils.model_type_to_model_dir(MODEL_TYPE_PROFILE)
    for d in pathlib.Path(trestle_root.joinpath(dir_name)).iterdir():
        if f"{product}-{cac_policy_id}" in d.name:
            res.append(
                ModelUtils.load_model_for_type(trestle_root, MODEL_TYPE_PROFILE, d.name)
            )

    return res


def load_all_controls(
    profiles: List[Tuple[Profile, pathlib.Path]],
    trestle_root: pathlib.Path,
) -> CatalogControlResolver:
    """
    Load all controls from OSCAL profiles.
    return loaded CatalogControlResolver
    """
    catalog_helper = CatalogControlResolver()
    for _, profile_path in profiles:
        profile_resolver = ProfileResolver()
        resolved_catalog = profile_resolver.get_resolved_profile_catalog(
            trestle_root,
            os.path.join(profile_path, "profile.json"),
            block_params=False,
            params_format="[.]",
            show_value_warnings=True,
        )
        catalog_helper.load(resolved_catalog)

    return catalog_helper
