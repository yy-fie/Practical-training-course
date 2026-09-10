CREATE TABLE [dbo].[stations]
(
	[station_id] [bigint] NULL,-- 站点ID
	[station_name] [text] NULL,-- 站点名称
	[line] [text] NULL,-- 线路
	[district] [text] NULL-- 区域
)


CREATE TABLE [dbo].[tripsInfo](
	[出站线路名称] [nvarchar](50) NULL,
	[出站区域名称] [nvarchar](50) NULL,
	[进站线路名称] [nvarchar](50) NULL,
	[进站区域名称] [nvarchar](50) NULL,
	[用户Id] [nvarchar](50) NULL,
	[用户所在地区] [bigint] NULL,
	[出生年月] [bigint] NULL,
	[性别] [nvarchar](50) NULL,
	[进站名] [nvarchar](50) NULL,
	[进站时间] [nvarchar](50) NULL,
	[出站名] [nvarchar](50) NULL,
	[出站时间] [nvarchar](50) NULL,
	[乘车类型] [bigint] NULL,
	[乘车金额] [bigint] NULL,
	[年龄段] [nvarchar](50) NULL,
	[乘车日期] [nvarchar](50) NULL,
	[乘车月份] [nvarchar](50) NULL
) ON [PRIMARY]


CREATE TABLE [dbo].[userInfo](
	[用户Id] [text] NULL,
	[用户所在地区] [bigint] NULL,
	[出生年月] [bigint] NULL,
	[性别] [bigint] NULL,
	[平均每月乘车金额] [float] NULL,
	[用户等级] [nvarchar](50) NULL,
	[用户年龄段] [nvarchar](50) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]




 




--部门表
create   table   DepartmentInfo
(
  departmentId  int   primary key  identity(1,1),---院系Id  主键
  departmentName   nvarchar(200)---院系名称
)




--角色表
create   table   RoleInfo
(
  roleId  int   primary key  identity(1,1),---角色Id  主键
  roleName   nvarchar(200)---角色名称
)


--学年表

create table AcademicYear
(
   yearId  int   primary key  identity(1,1),---学年Id  主键
   yearName   nvarchar(200),---学年名称（如：2023-2024学年）
   startDate  date,---开始日期
   endDate  date,---结束日期
   isCurrent  int   --是否当前学年（1:是，0:否）
)

--学期表
create table Semester
(
   semesterId  int   primary key  identity(1,1),---学期Id  主键
   semesterName   nvarchar(200),---学期名称（如：第一学期、第二学期）
   yearId  int,---学年Id（外键关联AcademicYear表）
   startDate  date,---开始日期
   endDate  date,---结束日期
   isCurrent  int,--是否当前学期（1:是，0:否）
   constraint FK_Semester_AcademicYear foreign key (yearId) references AcademicYear(yearId)---外键约束
)



--专业表

create table Major
(
   majorId  int   primary key  identity(1,1),---专业Id  主键
   majorName   nvarchar(200),---专业名称
   departmentId  int,---所属院系Id
   majorCode  nvarchar(50),---专业代码
   category  nvarchar(100)---学科门类
)



--年级表
create table Grade
(
   gradeId  int   primary key  identity(1,1),---年级Id  主键
   gradeName   nvarchar(200),---年级名称（如：2022级、2023级）
   entryYear  int,---入学年份
   departmentId  int,---院系Id
   majorId  int,---专业Id（外键关联Major表）
   classCount  int,--班级数量
   studentCount  int,--学生总数
   constraint FK_Grade_Major foreign key (majorId) references Major(majorId)---外键约束
)





create  table   UserInfo
(
   userId  int   primary key  identity(1,1),---用户Id  主键
   realName   nvarchar(200),---用户真实名
   phone  nvarchar(200),---用户手机号
   roleId  int,--角色Id
   departmentId  int   --院系Id

)

--UserInfo与RoleInfo绑定动作需要设置外键：    用户表（多端）上增加一端（角色表）的主键作为外键
alter  table UserInfo
add   constraint     User_Role_FK
foreign  key  (roleId)
references   RoleInfo(roleId)

alter  table UserInfo
add   constraint     User_Department_FK
foreign  key  (departmentId)
references    DepartmentInfo(departmentId)


-- 添加性别字段
ALTER TABLE UserInfo 
ADD gender nvarchar(10);---性别

-- 添加籍贯字段
ALTER TABLE UserInfo 
ADD nativePlace nvarchar(200);---籍贯

-- 添加政治面貌字段
ALTER TABLE UserInfo 
ADD politicalStatus nvarchar(50);--政治面貌
--添加登录密码
ALTER TABLE UserInfo 
ADD loginPassword nvarchar(200);---登录密码
--添加身份证号字段
ALTER TABLE UserInfo 
ADD idCard nvarchar(200);---身份证号
--添加邮箱字段
ALTER TABLE UserInfo 
ADD email nvarchar(200);---邮箱








CREATE TABLE [dbo].[UsersInfo](
	[userId] [int] IDENTITY(1,1) NOT NULL,--
	[realName] [nvarchar](200) NULL,--
	[phone] [nvarchar](200) NULL,--
	[roleId] [int] NULL,
	[departmentId] [int] NULL,
	[gender] [nvarchar](10) NULL,
	[nativePlace] [nvarchar](200) NULL,
	[politicalStatus] [nvarchar](50) NULL,
	[loginPassword] [nvarchar](200) NULL,
	[idCard] [nvarchar](200) NULL,
	[email] [nvarchar](200) NULL,
PRIMARY KEY CLUSTERED 
(
	[userId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]




--校区表
create   table   CampusInfo
(
  campusId  int   primary key  identity(1,1),---校区Id  主键
  campusName   nvarchar(200)---校区名称
)



--建筑表
create   table   BuildingInfo
(
  buildingId  int   primary key  identity(1,1),---建筑Id  主键
  buildingName   nvarchar(200),---建筑名称
  buildingCode   nvarchar(50),---建筑代码
  buildingAddress   nvarchar(200),---建筑地址
  buildingDescription   nvarchar(200)---建筑描述
)


--建筑楼层表
create   table   FloorInfo
(
  floorId  int   primary key  identity(1,1),---楼层Id  主键
  floorName   nvarchar(200),---楼层名称
  buildingId  int,---建筑Id（外键关联BuildingInfo表）
  floorDescription   nvarchar(200)---楼层描述
)
alter  table FloorInfo
add   constraint     Floor_Building_FK
foreign  key  (buildingId)
references   BuildingInfo(buildingId)


--房间表
create   table   RoomInfo
(
  roomId  int   primary key  identity(1,1),---房间Id  主键
  roomName   nvarchar(200),---房间名称
  floorId  int,---楼层Id（外键关联FloorInfo表）
  buildingId  int,---建筑Id（外键关联BuildingInfo表）
  roomType   nvarchar(50),---房间类型 1 学生宿舍 2 教师办公室 3 教学楼 4 实验楼 5 其他
  roomDescription   nvarchar(200)---房间描述
)

alter  table RoomInfo
add   constraint     Room_Floor_FK
foreign  key  (floorId)
references   FloorInfo(floorId)

alter  table RoomInfo
add   constraint     Room_Building_FK
foreign  key  (buildingId)
references   BuildingInfo(buildingId)

-- ==========================================
-- 学生信息表
-- ==========================================
create table StudentInfo
(
    studentId int primary key identity(1,1), -- 学生记录主键
    userId int unique not null,              -- 关联用户表的主键，设置唯一约束确保一个用户只能对应一个学生身份
    studentNo nvarchar(50) not null,         -- 学号
    entryYear int,                           -- 入学年份
    -- 外键约束
    constraint FK_Student_User foreign key (userId) references UserInfo(userId) 

)




-- ==========================================
-- 教师信息表
-- ==========================================
create table TeacherInfo
(
    teacherId int primary key identity(1,1), -- 教师记录主键
    userId int unique not null,              -- 关联用户表的主键，设置唯一约束
    teacherNo nvarchar(50) not null,         -- 工号/教工号
    title nvarchar(50),                      -- 职称（如：教授、副教授、讲师）
    hireDate date,                           -- 入职日期
    workYears int,                           -- 工龄（也可以通过当前日期 - hireDate 计算，建议存储入职日期更规范）

    
    -- 外键约束
    constraint FK_Teacher_User foreign key (userId) references UserInfo(userId) 

)


-- ==========================================
-- 课程表
-- ==========================================
create table CourseInfo
(
    courseId int primary key identity(1,1), -- 课程记录主键
    courseName nvarchar(100) not null      -- 课程名称
)


--  开课计划表 (CourseOffering)
create table CourseOffering
(
    offeringId int primary key identity(1,1), -- 开课ID
    
    -- 【设置课程】
    courseId int not null,            -- 关联 CourseInfo
    
    -- 【设置学期】
    semesterId int not null,          -- 关联 Semester
    
    -- 【设置教师】
    teacherId int not null,           -- 关联 TeacherInfo (直接使用教师表主键)

    -- 外键约束
    constraint FK_Offering_Course foreign key (courseId) references CourseInfo(courseId),
    constraint FK_Offering_Semester foreign key (semesterId) references Semester(semesterId),
    constraint FK_Offering_Teacher foreign key (teacherId) references TeacherInfo(teacherId)
)



CREATE TABLE [dbo].[Book](
	[bookId] [int] IDENTITY(1,1) NOT NULL, -- 图书ID
	[bookName] [nvarchar](1000) NULL, -- 图书名称
	[bookCategory] [nvarchar](1000) NULL, -- 图书类别
	[bookTag] [nvarchar](1000) NULL,	 -- 图书标签
	[Authors] [nvarchar](1000) NULL, -- 作者
	[Price] [decimal](18, 2) NULL,	 -- 价格
	[Url] [nvarchar](1000) NULL, -- 网址
	[Pic] [nvarchar](1000) NULL, -- 图片
	[Isbn] [nvarchar](50) NULL, -- ISBN
	[description] [nvarchar](max) NULL, -- 图书简介	
	[mulu] [nvarchar](max) NULL, -- 目录
	[publishDate] [date] NULL -- 出版日期
 CONSTRAINT [PK_Book] PRIMARY KEY CLUSTERED 
(
	[bookId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]