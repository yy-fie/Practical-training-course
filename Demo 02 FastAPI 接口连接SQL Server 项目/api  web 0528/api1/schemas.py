from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import date

class StationCreate(BaseModel):
    """创建站点请求模型"""
  
    station_name: Optional[str] = Field(None, description="站点名称")
    line: Optional[str] = Field(None, description="线路")
    district: Optional[str] = Field(None, description="区域")

class Station(BaseModel):
    """站点响应模型"""
    station_id: Optional[int] = Field(None, description="站点ID")
    station_name: Optional[str] = Field(None, description="站点名称")
    line: Optional[str] = Field(None, description="线路")
    district: Optional[str] = Field(None, description="区域")
    
    class Config:
        from_attributes = True

class StationList(BaseModel):
    """站点列表响应"""
    total: int
    rows: List[Station]

class TripStats(BaseModel):
    """站点乘车统计响应模型"""
    乘车月份: Optional[str] = Field(None, description="乘车月份")
    总金额: Optional[Decimal] = Field(None, description="总乘车金额")
    乘车次数: Optional[int] = Field(None, description="乘车次数")
    
    class Config:
        from_attributes = True

class TripStatsList(BaseModel):
    """站点乘车统计列表响应"""
    total: int
    station_name: str
    data: List[TripStats]


class Book(BaseModel):
    bookId: int
    bookName: Optional[str] = None
    bookCategory: Optional[str] = None
    bookTag: Optional[str] = None
    Authors: Optional[str] = None
    Price: Optional[float] = None
    Url: Optional[str] = None
    Pic: Optional[str] = None
    Isbn: Optional[str] = None
    description: Optional[str] = None
    mulu: Optional[str] = None
    publishDate: Optional[date] = None
    
    class Config:
        from_attributes = True

class BookCreate(BaseModel):
    bookName: Optional[str] = None
    bookCategory: Optional[str] = None
    bookTag: Optional[str] = None
    Authors: Optional[str] = None
    Price: Optional[float] = None
    Url: Optional[str] = None
    Pic: Optional[str] = None
    Isbn: Optional[str] = None
    description: Optional[str] = None
    mulu: Optional[str] = None
    publishDate: Optional[date] = None

class BookList(BaseModel):
    total: int
    rows: List[Book]



class BuildingCreate(BaseModel):
    """创建建筑的数据模型"""
    buildingName: str = Field(..., description="建筑名称")
    buildingCode: Optional[str] = Field(None, description="建筑代码")
    buildingAddress: Optional[str] = Field(None, description="建筑地址")
    buildingDescription: Optional[str] = Field(None, description="建筑描述")


class Building(BaseModel):
    """建筑数据模型"""
    buildingId: int
    buildingName: str
    buildingCode: Optional[str] = None
    buildingAddress: Optional[str] = None
    buildingDescription: Optional[str] = None


class BuildingList(BaseModel):
    """建筑列表响应模型"""
    total: int
    rows: List[Building]


class UserCreate(BaseModel):
    """创建用户的数据模型"""
    realName: Optional[str] = Field(None, description="真实姓名")
    phone: Optional[str] = Field(None, description="手机号")
    roleId: Optional[int] = Field(None, description="角色ID")
    departmentId: Optional[int] = Field(None, description="部门ID")
    gender: Optional[str] = Field(None, description="性别")
    nativePlace: Optional[str] = Field(None, description="籍贯")
    politicalStatus: Optional[str] = Field(None, description="政治面貌")
    loginPassword: Optional[str] = Field(None, description="登录密码")
    idCard: Optional[str] = Field(None, description="身份证号")
    email: Optional[str] = Field(None, description="邮箱")


class User(BaseModel):
    """用户数据模型"""
    userId: int
    realName: Optional[str] = None
    phone: Optional[str] = None
    roleId: Optional[int] = None
    departmentId: Optional[int] = None
    gender: Optional[str] = None
    nativePlace: Optional[str] = None
    politicalStatus: Optional[str] = None
    loginPassword: Optional[str] = Field(default=None, exclude=True)
    idCard: Optional[str] = None
    email: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserList(BaseModel):
    """用户列表响应模型"""
    total: int
    rows: List[User]


class FloorCreate(BaseModel):
    """创建楼层的数据模型"""
    floorName: Optional[str] = Field(None, description="楼层名称")
    buildingId: Optional[int] = Field(None, description="所属建筑ID")
    floorDescription: Optional[str] = Field(None, description="楼层描述")


class Floor(BaseModel):
    """楼层数据模型"""
    floorId: int
    floorName: Optional[str] = None
    buildingId: Optional[int] = None
    floorDescription: Optional[str] = None

    class Config:
        from_attributes = True


class FloorList(BaseModel):
    """楼层列表响应模型"""
    total: int
    rows: List[Floor]


class MajorCreate(BaseModel):
    """创建专业的数据模型"""
    majorName: Optional[str] = Field(None, description="专业名称")
    departmentId: Optional[int] = Field(None, description="所属院系ID")
    majorCode: Optional[str] = Field(None, description="专业代码")
    category: Optional[str] = Field(None, description="学科门类")


class Major(BaseModel):
    """专业数据模型"""
    majorId: int
    majorName: Optional[str] = None
    departmentId: Optional[int] = None
    majorCode: Optional[str] = None
    category: Optional[str] = None
    departmentName: Optional[str] = None

    class Config:
        from_attributes = True


class MajorList(BaseModel):
    """专业列表响应模型"""
    total: int
    rows: List[Major]

class PasswordChange(BaseModel):
    """修改个人密码请求模型"""
    oldPassword: str = Field(..., max_length=128, description="原始密码")
    newPassword: str = Field(..., max_length=128, description="修改后密码")
    confirmPassword: str = Field(..., max_length=128, description="确认修改后密码")
