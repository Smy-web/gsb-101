# 生态缸造景设计会议 · 素材库与案例库后端

「生态缸造景设计会议」全栈应用的一个后端子集。上游项目里，前端展示苔藓与沉木素材、ADA 风格造景案例，设计师和客户在会议里聊方案，后端还要做水声降噪、Whisper 转写、发言者分离、AI 摘要和作品证书。本仓库只保留素材库与案例库这两组 REST 接口和它们共用的数据层，路径已从上游的 `backend/` 提到仓库根。音频、AI 摘要、证书、会议与聊天模块都不在本仓库范围内。

## 目录

    database.py             SQLAlchemy engine / SessionLocal / get_db 依赖
    models.py               ORM 模型（用户、素材、案例、会议、消息、录音、摘要）
    schemas.py              Pydantic 请求与响应模型
    routers/materials.py    素材接口，挂载前缀 /api/materials，内含 8 条演示素材
    routers/cases.py        案例接口，挂载前缀 /api/cases，内含 5 条演示案例
    tests/                  pytest 测试，TestClient + tmp_path 下的 sqlite

`routers/__init__.py` 是空文件，上游那个会把四个路由一次性 import 进来的 `main.py` 没有携带（它引用了裁剪范围之外的音频与 AI 模块）。测试里自己起一个 `FastAPI()`，把需要的 router `include_router` 进去即可。

## 路由

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/materials/` | 素材列表，可按 `category` 过滤 |
| GET | `/api/materials/{material_id}` | 单个素材，不存在返回 404 |
| GET | `/api/materials/categories` | 素材分类清单，前端筛选条直接用它渲染 |
| POST | `/api/materials/` | 新建素材 |
| PUT | `/api/materials/{material_id}` | 全量更新素材 |
| DELETE | `/api/materials/{material_id}` | 删除素材 |
| GET | `/api/cases/` | 案例列表，可按 `style`、`difficulty` 过滤 |
| GET | `/api/cases/{case_id}` | 单个案例，不存在返回 404 |
| GET | `/api/cases/styles` | 造景风格清单，前端筛选条直接用它渲染 |
| POST | `/api/cases/` | 新建案例 |
| PUT | `/api/cases/{case_id}` | 全量更新案例 |
| DELETE | `/api/cases/{case_id}` | 删除案例 |

## 业务约定

- 演示数据：两组接口各有一份写死在模块里的演示数据（8 条素材、5 条案例），当初是为了库空的时候前端也能出图。它现在算什么，由你定并写进下面的「选定方案」：是首次启动写库的种子数据，还是只在库空时顶上的只读回退，或者别的口径。不管选哪种，同一条记录在列表、详情、更新、删除这四个入口的可见性必须一致，筛选条件的语义也不能因为走了演示数据就变。

  > 选定方案：**种子数据**。每个接口在处理请求前先检查对应的表，表为空就把演示数据原样落库（保留原 id，案例的 `created_at` 按 ISO 字符串解析成时间），之后列表、详情、更新、删除全部只走数据库。选它的理由：四个入口的可见性天然一致，不存在「详情看得到、改删 404」；新记录的自增 id 从种子之后继续分配，不会和任何可见记录撞号；筛选语义只有一套，不存在「走演示数据就变味」的问题。相比只读回退，它不需要给演示数据单独搞一套只读语义，前端也不用置灰编辑按钮。注意一个推论：如果库里的记录被全部删除，下一次请求会重新播种，视同回到初始状态。

- 分类与风格清单是前端筛选条的唯一数据来源：前端先拉 `/categories`（或 `/styles`），再把清单里的值原样当查询参数拉列表。所以清单必须能正常取到，清单里的每个取值都要能筛出对应的记录，反过来，落库的 `category` / `style` 也必须能在清单里找到，否则前台永远筛不出这条数据。

  > 清单方案：**动态生成**。`/categories` 返回内置六项（`苔藓、沉木、底床、石材、水草、设备`）加上库里实际出现过、但不在内置项里的其他取值（去重、按字典序排在内置项之后）；`/styles` 同理，内置六项为 `ADA自然风格、Iwagumi石景风格、荷兰景风格、凹形构图风格、凸形构图风格、中式山水风格`。写入时不校验 `category` / `style` 的取值范围，新值保存成功后自动出现在清单里、立刻可筛。对已有数据的影响：无，清单是只读派生的，不改写任何已落库的记录；内置项即使没有对应记录也始终出现在清单里，筛它们时按下面的口径返回空列表。

- 过滤参数的匹配口径（`category` / `style` / `difficulty` 一致）：

  > - 完全不传参数：不过滤，返回全部记录。
  > - 传空字符串或只含空白字符：等同未传，不过滤。
  > - 首尾空格：先去掉再匹配（`%20苔藓%20` 能匹配 `苔藓`）。
  > - 大小写：不敏感（`ada自然风格` 能匹配 `ADA自然风格`；中文本身无大小写，只影响 ASCII 字母）。
  > - 按以上口径归一化后命中为空：返回空列表 `[]`，绝不回退成未筛选的数据。
  > - 列表顺序：一律按 `id` 升序返回。

- 错误口径：记录不存在时，详情、更新、删除都返回 404，detail 为 `Material not found` / `Case study not found`；路径参数不是整数时由框架返回 422。本次没有新增写校验（清单采用动态生成方案），因此没有新增 4xx 文案；任何输入都不应产生未捕获的 500。
- `Material.properties` 是 JSON 列，键是中文（难度、光照需求、CO2需求、生长速度、适宜温度）；`CaseStudy` 的 `gallery_urls` / `materials_used` / `plants` 也是 JSON 列。
- 404 的 detail 文案（`Material not found` / `Case study not found`）已被前端和运维脚本硬编码匹配，不要改。
- `price` 是中文字符串（`¥30/份`、`¥80-¥200`），不是数字，不要改类型，也不要在接口里做汇率或区间解析。
- 列表接口的注册路径带尾斜杠（`/api/materials/`），前端调的是不带尾斜杠的 `/api/materials`，靠框架的 307 重定向兜住。路由路径、HTTP 方法、请求与响应字段名都不要动。
- 案例的 `created_at` 由 ORM 默认值填；演示数据里的 `created_at` 是 ISO 字符串。响应模型会统一序列化，调用方看到的都是 ISO 字符串。

## 运行与测试

依赖版本见 `requirements-task.txt`。运行环境使用预装好的共享虚拟环境，不要现场安装：

    ~/venvs/gsb-aqua/bin/python -m pytest tests/ -q

数据库默认 `sqlite:///./aquascape.db`，可用环境变量 `DATABASE_URL` 覆盖。测试请用 `tmp_path` 下的 sqlite 文件，通过 `app.dependency_overrides` 覆盖 `get_db`，自己 `create_all` 建表；跑完整套测试之后仓库工作树应当保持干净，不留 `aquascape.db`，也不留别的产物。测试不得联网，素材图片是外链 URL，不要真的去请求。
