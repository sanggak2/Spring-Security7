package com.example.login.controller;

import com.example.login.dto.ChatDto; // 방금 만든 DTO 임포트
import com.example.login.service.ChatService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    @Autowired
    private ChatService chatService;

    @PostMapping
    public String chat(@RequestBody ChatDto request) {
        return chatService.getChatResponse(request.getMessage());
    }
}