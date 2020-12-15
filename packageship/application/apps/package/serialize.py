#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
Description: marshmallow serialize
"""
from marshmallow import Schema
from marshmallow import fields
from marshmallow import ValidationError
from marshmallow import validate

from packageship.application.models.package import Packages


def validate_pagenum(pagenum):
    """
    Description: Method test
    Args：
        pagenum: pagenum
    Returns:
        True or failure
    Raises:
        ValidationError: Test failed
    """
    if pagenum <= 0 or pagenum > 65535:
        raise ValidationError("pagenum is illegal data ")


def validate_pagesize(pagesize):
    """
    Description: Method test
    Args：
        pagesize: pagesize
    Returns:
        True or failure
    Raises:
        ValidationError: Test failed
    """
    if pagesize <= 0 or pagesize > 65535:
        raise ValidationError("pagesize is illegal data ")


def validate_maintainlevel(maintainlevel):
    """
    Description: Method test
    Args：
        maintainlevel: maintainlevel
    Returns:
        True or failure
    Raises:
        ValidationError: Test failed
    """
    if maintainlevel not in [1, 2, 3, 4, '']:
        raise ValidationError("maintainLevel is illegal data ")


def validate_maintainlevels(maintainlevel):
    """
    Description: Method test
    Args：
        maintainlevel: maintainlevel
    Returns:
        True or failure
    Raises:
        ValidationError: Test failed
    """
    if maintainlevel not in ['1', '2', '3', '4', '']:
        raise ValidationError("maintainLevel is illegal data ")


class AllPackagesSchema(Schema):
    """
    Description: AllPackagesSchema serialize
    """
    table_name = fields.Str(
        required=True,
        validate=validate.Length(min=1,
                                 max=200))
    page_num = fields.Integer(
        required=True,
        validate=validate_pagenum
    )
    page_size = fields.Integer(
        required=True,
        validate=validate_pagesize
    )
    query_pkg_name = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)
    maintainner = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)
    maintainlevel = fields.Str(
        validate=validate_maintainlevels,
        required=False,
        allow_none=True)


class SinglepackSchema(Schema):
    """
    Description: GetpackSchema serialize
    """
    pkg_name = fields.Str(
        required=True,
        validate=validate.Length(min=1,
                                 max=200))

    table_name = fields.Str(required=True,
                            validate=validate.Length(min=1,
                                                     max=200))


class UpdatePackagesSchema(Schema):
    """
    Description: UpdatePackagesSchema serialize
    """
    pkg_name = fields.Str(
        required=False,
        validate=validate.Length(
            max=200))
    maintainer = fields.Str(validate=validate.Length(
        max=50), required=False, allow_none=True)
    maintainlevel = fields.Integer(
        validate=validate_maintainlevel,
        required=False,
        allow_none=True)
    batch = fields.Boolean(
        required=True)
    filepath = fields.Str(validate=validate.Length(
        max=200), required=False, allow_none=True)


def validate_level(level):
    """
    Description: the default value of level is -1, then query all the install depend.
    When user input level > 0, then query the corresponding level of install depend
    Args：
    Returns:
    Raises: ValidationError
    """
    if int(level) < -1 or int(level) == 0:
        raise ValidationError("level is illegal data ")


class InstallDependSchema(Schema):
    """
    Description: InstallDependSchema
    """
    binaryName = fields.List(
        fields.String(),
        required=True, validate=validate.Length(min=1, max=500))
    db_list = fields.List(fields.String(), required=False, allow_none=True)
    level = fields.Integer(validate=validate_level, required=False, allow_none=True)


class BuildDependSchema(Schema):
    """
    Description: BuildDependSchema serialize
    """
    sourceName = fields.List(fields.String(validate=validate.Length(
        min=1, max=200)), required=True, allow_none=False)
    db_list = fields.List(fields.String(), required=False, allow_none=True)
    level = fields.Integer(validate=validate_level, required=False, allow_none=True)


def validate_withsubpack(withsubpack):
    """
    Description: Method test
    Args：
        withsubpack: withsubpack
    Returns:
        True or failure
    Raises:
        ValidationError: Test failed
    """
    if withsubpack not in ['0', '1']:
        raise ValidationError("withSubpack is illegal data ")


class BeDependSchema(Schema):
    """
    Description: BeDependSchema serialize
    """
    packagename = fields.List(fields.String(validate=validate.Length(
        min=1, max=200)), required=True, allow_none=False)
    withsubpack = fields.Str(
        validate=validate_withsubpack,
        required=False, allow_none=True)
    dbname = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=50))
    level = fields.Integer(validate=validate_level, required=False, allow_none=True)


def validate_selfbuild(selfbuild):
    """
    Description: Method test
    """
    if selfbuild not in ['0', '1']:
        raise ValidationError("selfbuild is illegal data ")


def validate_packtype(packtype):
    """
    Description: Method test
    """
    if packtype not in ['source', 'binary']:
        raise ValidationError("packtype is illegal data ")


class SelfDependSchema(Schema):
    """
    Description: SelfDependSchema serialize
    """
    packagename = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))
    db_list = fields.List(fields.String(), required=False, allow_none=True)
    selfbuild = fields.Str(validate=validate_selfbuild,
                           required=False, allow_none=True)
    withsubpack = fields.Str(
        validate=validate_withsubpack, required=False, allow_none=True)
    packtype = fields.Str(validate=validate_packtype,
                          required=False, allow_none=True)


class DeletedbSchema(Schema):
    """
    Description: DeletedbSchema serialize
    """
    dbName = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=200))


def have_err_db_name(db_list, db_priority):
    """
    Description: have error database name method
    Args:
        db_list: db_list db list of inputs
        db_priority: db_priority default list
    Returns:
        If any element in db_list  is no longer in db_priority, return false
    Raises:
    """
    return any(filter(lambda db_name: db_name not in db_priority, db_list))


class InitSystemSchema(Schema):
    """
    Description: InitSystemSchema serialize
    """
    configfile = fields.Str(
        validate=validate.Length(
            max=500), required=False, allow_none=True)


class AllPackInfoSchema(Schema):  # pylint: disable= too-few-public-methods
    """
        Field serialization for package file download
    """
    class Meta:
        """Model mapping serialized fields"""
        model = Packages
        fields = (
            'id',
            'name',
            'url',
            'version',
            'release',
            'release_time',
            'rpm_license',
            'maintainer',
            'maintainlevel',
            'feature',
            'release_time',
            'used_time',
            'maintainer_status',
            'latest_version',
            'latest_version_time')


class SinglePackInfoSchema(Schema):
    """
        Field serialization for package file download
    """

    class Meta:
        """Model mapping serialized fields"""
        model = Packages
        fields = (
            'name',
            'version',
            'release',
            'url',
            'feature',
            'rpm_license',
            'summary',
            'description')


class DataFormatVerfi(Schema):
    """
    Verify the data in yaml
    """

    maintainer = fields.Str(validate=validate.Length(
        max=50), required=False, allow_none=True)
    maintainlevel = fields.Int(
        validate=validate_maintainlevel,
        required=False,
        allow_none=True)
    name = fields.Str(validate=validate.Length(min=1,
                                               max=50), required=True)
