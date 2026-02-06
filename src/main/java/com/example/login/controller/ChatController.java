package com.example.login.controller;

import com.example.login.dto.ChatDto; // 방금 만든 DTO 임포트
import com.example.login.service.ChatService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Chat Api Controller", description = "챗봇 api컨트롤러입니다")
@RestController
@RequestMapping("/api/chat")
public class ChatController {

    @Autowired
    private ChatService chatService;

    @Operation(summary = "챗봇api", description = "챗봇api입니다")
    @PostMapping
    public String chat(@RequestBody ChatDto request) {
        return chatService.getChatResponse(request.getMessage());
    }
}