package com.example.login.config;

import lombok.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.access.hierarchicalroles.RoleHierarchy;
import org.springframework.security.access.hierarchicalroles.RoleHierarchyImpl;
import org.springframework.security.authorization.AuthorizationDecision;
import org.springframework.security.authorization.AuthorizationManager;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.intercept.RequestAuthorizationContext;

@Configuration
public class SecurityConfig {
    // 비밀번호 암호화
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    // Role 하이라키
    @Bean
    public RoleHierarchy roleHierarchy() {
        return RoleHierarchyImpl.withRolePrefix("ROLE_")
                .role("ADMIN").implies("USER")
                .build();
    }

    // 시큐리티 필터 구현
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) {
        // CSRF
        http
                .csrf(csrf -> csrf
                        .ignoringRequestMatchers("/logout"));
        // 로그인 필터
        http
                .formLogin(login -> login
                        .loginProcessingUrl("/login")
                        .loginPage("/login")
                        .defaultSuccessUrl("/", true));

        // 로그아웃 필터
        http
                .logout(logout -> logout
                        .logoutUrl("/logout")
                        .logoutSuccessUrl("/login")
                        .invalidateHttpSession(true)
                        .deleteCookies("JSESSIONID", "remember-me") // 쿠키 삭제
                );

        // remember me 설정
        http
                .rememberMe(me -> me
                        .key("remember-me")
                        .rememberMeParameter("remember-me")
                        .tokenValiditySeconds(14 * 24 * 60 * 60));
        
        // 인가 필터
        /**
         * requestMatchers("특정 경로나 와일드카드 아무거나 /post/**")
         * permitAll() : 전부 허용
         * has(All/Any)Role(ex."Admin")
         * denyAll()
         * authenticated()
         */
        http    
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                        .requestMatchers(/*HttpMethod.GET, Get요청만 받을 수도 잇음*/"/").permitAll()
                        .requestMatchers("/join","/login").anonymous()
                        .requestMatchers("/user").hasAnyRole("USER") // 둘 중 하나 가지고 있으면 접근 가능
                        .requestMatchers("/admin").access(customAuthorizationManager())
                        .anyRequest().denyAll()
                )
                .exceptionHandling(ex -> ex
                        // /login, /join 접근 시 거부당하면 "/" 로 리다이렉트
                        .defaultAccessDeniedHandlerFor(
                                (request, response, e) -> response.sendRedirect("/"),
                                request -> {
                                    String uri = request.getRequestURI();
                                    return uri.equals("/login") || uri.equals("/join");
                                }
                        )
        );;

        // 세션
        //stateless(jwt설정할때)
//        http
//                .sessionManagement(session -> session
//                .sessionCreationPolicy(SessionCreationPolicy.STATELESS));
        http
                .sessionManagement(session -> session
                        .sessionFixation().changeSessionId());

        // 최종 빌드
        return http.build();
    }
    // 커스텀 access 인가
    private AuthorizationManager<RequestAuthorizationContext> customAuthorizationManager() {
        return ((authentication, context) ->
        {
            boolean allowed =
                    authentication.get().getAuthorities().stream()
                            .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));
            // 지역 / 비즈니스, 개인 인지 / 사용 카운트 등 복잡하게 만들 수 있다.

            return new AuthorizationDecision(allowed);
        });
    }
}
