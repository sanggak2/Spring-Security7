# 자바 17
FROM eclipse-temurin:17-jdk

# 작업 디렉토리
WORKDIR /app

# 빌드된 JAR 파일 컨테이너로 복사
COPY build/libs/*-SNAPSHOT.jar app.jar

# 컨테이너 시작될 때 명령어
ENTRYPOINT ["java", "-jar", "app.jar"]