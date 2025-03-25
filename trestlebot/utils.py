# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Common utility functions."""
from typing import Any, List

from ruamel.yaml import CommentedMap, CommentToken


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
