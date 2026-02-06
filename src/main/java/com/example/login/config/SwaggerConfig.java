package com.example.login.config;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springdoc.core.models.GroupedOpenApi;
import org.springdoc.core.utils.SpringDocUtils;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.ui.Model;

import java.security.Principal;

@Configuration
public class SwaggerConfig {

    static {
        SpringDocUtils.getConfig()
                // 1. 특정 어노테이션 숨김
                .addAnnotationsToIgnore(AuthenticationPrincipal.class)

                // 2. 특정 타입의 파라미터 숨김
                .addRequestWrapperToIgnore(
                        UserDetails.class,
                        Authentication.class,
                        Principal.class,
                        Model.class
                );
    }

    @Bean
    public OpenAPI openAPI() {
        return new OpenAPI()
                .components(new Components())
                .info(apiInfo());
    }

    private Info apiInfo() {
        return new Info()
                .title("Spring Boot API Test") // 문서 제목
                .description("Swagger UI 테스트 문서입니다.") // 문서 설명
                .version("1.0.0"); // 버전
    }

//    // 사용자용 API 그룹
//    @Bean
//    public GroupedOpenApi userGroup() {
//        return GroupedOpenApi.builder()
//                .group("1. 사용자 API")
//                .pathsToMatch("/user/**", "/join", "/login", "/")
//                .build();
//    }
//
//    // 관리자용 API 그룹
//    @Bean
//    public GroupedOpenApi adminGroup() {
//        return GroupedOpenApi.builder()
//                .group("2. 관리자 API")
//                .pathsToMatch("/admin/**")
//                .build();
//    }
}
