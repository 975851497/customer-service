所有文件已创建完成。下面是完整的部署方案总结：                  
                                                                                          
  ---                 
  项目结构（新增/修改的文件）                                                                                                                                                                                                                        
   
  edu-data/                                                                                                                                                                                                                                          
  ├── Dockerfile                     ← 新增：FastAPI 应用容器镜像                                                                                                                                                                                  
  ├── .gitignore                                                                                                                                                                                                                                     
  ├── docker/                                                                                                                                                                                                                                        
  │   ├── docker-compose.yaml        ← 修改：新增 api 服务                                                                                                                                                                                           
  │   └── entrypoint.sh              ← 新增：容器启动脚本
  └── ...

  各阶段使用方式

  阶段一：本地开发（宿主机跑智能客服）

  cd edu-data/docker
  docker compose up -d mysql    # 只启动 MySQL

  宿主机上的智能客服系统直接访问：
  - MySQL → 127.0.0.1:3306
  - Edu API → 127.0.0.1:8000（或在宿主机上 uv run -m app.main 启动）

  阶段二：部署到同一台虚拟机

  # 将项目传到虚拟机
  scp -r edu-data user@vm-ip:/opt/edu-data/

  # SSH 登录后
  cd /opt/edu-data/docker
  docker compose up -d    # 启动 MySQL + API

  # 首次启动会自动：
  # 1. 等待 MySQL 就绪
  # 2. 初始化数据库（建表）
  # 3. 生成全量业务数据
  # 4. 启动 FastAPI 服务（端口 8000）

  # 验证
  curl http://vm-ip:8000/health
  curl http://vm-ip:8000/docs

  阶段三：分离到两台服务器

  ┌────────────────┬──────────────┬──────────┐
  │     服务器     │     服务     │ 暴露端口 │
  ├────────────────┼──────────────┼──────────┤
  │ VM1 (10.0.0.1) │ MySQL        │ 3306     │
  ├────────────────┼──────────────┼──────────┤
  │ VM2 (10.0.0.2) │ FastAPI API  │ 8000     │
  ├────────────────┼──────────────┼──────────┤
  │ VM3 (将来)     │ 智能客服系统 │ -        │
  └────────────────┴──────────────┴──────────┘

  只需要修改 docker-compose.yaml 中的连接配置：
  - 如果 MySQL 分离出去，api 服务的 DB_HOST 改为 VM1 的 IP

  其他常用命令

  # 查看日志
  docker compose logs -f api

  # 单独重启 API（不重启 MySQL）
  docker compose restart api

  # 重置全部数据
  docker compose down -v
  docker compose up -d

  # 仅重建 API 镜像（代码修改后）
  docker compose build api
  docker compose up -d api

  ---
  需要调整的地方随时说，比如初始化数据量大小（现在用 --profile full）、端口映射、或 MySQL 密码等配置。
