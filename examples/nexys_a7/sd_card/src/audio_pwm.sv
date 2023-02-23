`timescale 1ns / 1ps
// Audio PWM module.

module audio_PWM(
    input clk, 			// 100MHz clock.
    input reset,		// Reset assertion.
    input [7:0] music_data,	// 8-bit music sample
    output reg PWM_out		// PWM output. Connect this to ampPWM.
    );
    
    
    reg [7:0] pwm_counter = 8'd0;           // counts up to 255 clock cycles per pwm period
       
          
    always @(posedge clk) begin
        if(reset) begin
            pwm_counter <= 0;
            PWM_out <= 0;
        end
        else begin
            pwm_counter <= pwm_counter + 1;
            
            if(pwm_counter >= music_data) PWM_out <= 0;
            else PWM_out <= 1;
        end
    end
endmodule
