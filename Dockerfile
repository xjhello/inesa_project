# 基础镜像
#FROM ubuntu_python2_svn:1.0
FROM 10.200.43.177:5000/ubuntu_python2_svn
# 复制代码
COPY . /usr/src/project-server
# 安装包
WORKDIR /usr/src/project-server

# 安装python第三方库
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt

# 容器对外开放端口
EXPOSE 8082
# MongoDB的环境变量，启动容器时，-e mongo_ip=10.200.43.160
COPY docker-entrypoint.sh /usr/local/bin
#RUN ln -s /usr/local/bin/docker-entrypoint.sh /
ENTRYPOINT ["docker-entrypoint.sh"]
# 开启ai
WORKDIR /usr/src/project-server/restful
CMD ["python","api.py"]
