package com.example.login.controller;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Tag(name = "예제 API", description = "Swagger 테스트입니다.")  // 1. 컨트롤러 설명
@Controller
public class SampleController {
    @Operation(summary = "문자열 반환", description = "파라미터로 받은 문자열 + 로그인 역할 + 메시지")   // 2. API 설명
    @GetMapping("/")
    public String index(@AuthenticationPrincipal UserDetails user,
            @Parameter(description = "인사말을 입력하세요", example = "안녕") // 3. 파라미터 설명
            @RequestParam(required = false, defaultValue = " ") String message,
                        Model model) {
        if (user != null) {
            // 로그인 한 사람
            System.out.println("로그인 유저: " + user.getUsername());
            model.addAttribute("username", user.getUsername());
            model.addAttribute("role", user.getAuthorities().toString());
        } else {
            // 로그인 안 한 사람
            System.out.println("로그인 안 함");
            model.addAttribute("username", "손님");
            model.addAttribute("role", "Guest");
        }
        model.addAttribute("message", message);
//        System.out.println(username + " : " + role + " : " + message);
        return "index";
    }

    @GetMapping("/user")
    public String user() {
        return "user";
    }

    @GetMapping("/admin")
    public String admin() {
        return "admin";
    }

}
