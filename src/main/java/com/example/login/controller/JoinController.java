package com.example.login.controller;

import com.example.login.domain.user.dto.UserDto;
import com.example.login.domain.user.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

@Tag(name = "Register Controller", description = "회원가입 컨트롤러 입니다.")
@Controller
public class JoinController {
    @Autowired
    private UserService userService;

    // 회원 가입 데이터 처리 메소드
    @Operation(summary = "회원가입", description = "회원가입 수행")
    @PostMapping("/join")
    public String join(UserDto dto) {
        userService.join(dto);
        return "redirect:/";
    }

    // 회원 가입 페이지 제공 메소드
    @GetMapping("/join")
    public String joinPage() {
        return "join";
    }
}
