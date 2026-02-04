package com.example.login.controller;

import com.example.login.domain.user.dto.UserDto;
import com.example.login.domain.user.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
public class JoinController {
    @Autowired
    private UserService userService;

    // 회원 가입 데이터 처리 메소드
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
