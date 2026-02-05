package com.example.login.domain.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserDto {
    @Schema(description = "아이디", example = "sanggak")
    private String username;
    @Schema(description = "비번", example = "1234")
    private String password;
}
