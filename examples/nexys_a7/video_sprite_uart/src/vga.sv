
/* vga: Generate VGA display signals (1024 x 768 @ 60Hz)
 *
 *                              ---- HORIZONTAL -----     ------VERTICAL -----
 *                              Active                    Active
 *                    Freq      Video   FP  Sync   BP      Video   FP  Sync  BP
 *   640x480, 60Hz    25.175    640     16    96   48       480    11   2    31
 *   800x600, 60Hz    40.000    800     40   128   88       600     1   4    23
 *   1024x768, 60Hz   65.000    1024    24   136  160       768     3   6    29
 *   1280x1024, 60Hz  108.00    1280    48   112  248       768     1   3    38
 *   1280x720p 60Hz   75.25     1280    72    80  216       720     3   5    30
 *   1920x1080 60Hz   148.5     1920    88    44  148      1080     4   5    36
 *
 * change the clock frequency, front porches, sync's, and back porches to create
 * other screen resolutions
 */

module vga(
  input wire pixel_clk_in,
  output logic [10:0] hcount_out,    // pixel number on current line
  output logic [9:0]  vcount_out,    // line number
  output logic vsync_out, hsync_out,
  output logic blank_out);

  parameter DISPLAY_WIDTH  = 1024;      // display width
  parameter DISPLAY_HEIGHT = 768;       // number of lines

  parameter  H_FP = 24;                 // horizontal front porch
  parameter  H_SYNC_PULSE = 136;        // horizontal sync
  parameter  H_BP = 160;                // horizontal back porch

  parameter  V_FP = 3;                  // vertical front porch
  parameter  V_SYNC_PULSE = 6;          // vertical sync
  parameter  V_BP = 29;                 // vertical back porch

  // horizontal: 1344 pixels total
  // display 1024 pixels per line
  logic hblank,vblank;
  logic hsyncon,hsyncoff,hreset,hblankon;
  assign hblankon = (hcount_out == (DISPLAY_WIDTH -1));
  assign hsyncon = (hcount_out == (DISPLAY_WIDTH + H_FP - 1));  //1047
  assign hsyncoff = (hcount_out == (DISPLAY_WIDTH + H_FP + H_SYNC_PULSE - 1));  // 1183
  assign hreset = (hcount_out == (DISPLAY_WIDTH + H_FP + H_SYNC_PULSE + H_BP - 1));  //1343

  // vertical: 806 lines total
  // display 768 lines
  logic vsyncon,vsyncoff,vreset,vblankon;
  assign vblankon = hreset & (vcount_out == (DISPLAY_HEIGHT - 1));   // 767
  assign vsyncon = hreset & (vcount_out == (DISPLAY_HEIGHT + V_FP - 1));  // 771
  assign vsyncoff = hreset & (vcount_out == (DISPLAY_HEIGHT + V_FP + V_SYNC_PULSE - 1));  // 777
  assign vreset = hreset & (vcount_out == (DISPLAY_HEIGHT + V_FP + V_SYNC_PULSE + V_BP - 1)); // 805

  // sync and blanking
  logic next_hblank,next_vblank;
  assign next_hblank = hreset ? 0 : hblankon ? 1 : hblank;
  assign next_vblank = vreset ? 0 : vblankon ? 1 : vblank;
  always_ff @(posedge pixel_clk_in) begin
    hcount_out <= hreset ? 0 : hcount_out + 1;
    hblank <= next_hblank;
    hsync_out <= hsyncon ? 0 : hsyncoff ? 1 : hsync_out;  // active low

    vcount_out <= hreset ? (vreset ? 0 : vcount_out + 1) : vcount_out;
    vblank <= next_vblank;
    vsync_out <= vsyncon ? 0 : vsyncoff ? 1 : vsync_out;  // active low

    blank_out <= next_vblank | (next_hblank & ~hreset);
  end
endmodule