$00 constant NOP      $2B constant RASET    $C2 constant PWCTR3
$01 constant SWRESET  $2C constant RAMWR    $C3 constant PWCTR4
$04 constant RDDID    $2E constant RAMRD    $C4 constant PWCTR5
$09 constant RDDST    $30 constant PTLAR    $C5 constant VMCTR1
$10 constant SLPIN    $36 constant MADCTL   $DA constant RDID1
$11 constant SLPOUT   $3A constant COLMOD   $DB constant RDID2
$12 constant PTLON    $B1 constant FRMCTR1  $DC constant RDID3
$13 constant NORON    $B2 constant FRMCTR2  $DD constant RDID4
$20 constant INVOFF   $B3 constant FRMCTR3  $E0 constant GMCTRP1
$21 constant INVON    $B4 constant INVCTR   $E1 constant GMCTRN1
$28 constant DISPOFF  $B6 constant DISSET5  $FC constant PWCTR6
$29 constant DISPON   $C0 constant PWCTR1
$2A constant CASET    $C1 constant PWCTR2
$80 constant DELAY

here constant init-table
    SWRESET       ,   DELAY ,           \ Software reset, 0 args, w/delay
      60 ,                             
    SLPOUT        ,   DELAY ,           \ Out of sleep mode, 0 args, w/delay
      60 ,                            
    FRMCTR1       , 3      ,            \ Frame rate ctrl - normal mode, 3 args:
      0x01 , 0x2C , 0x2D ,              \ Rate = fosc/(1x2+40) * (LINE+2C+2D)
    FRMCTR2       , 3      ,            \ Frame rate control - idle mode, 3 args:
      0x01 , 0x2C , 0x2D ,              \ Rate = fosc/(1x2+40) * (LINE+2C+2D)
    FRMCTR3       , 6      ,            \ Frame rate ctrl - partial mode, 6 args:
      0x01 , 0x2C , 0x2D ,              \ Dot inversion mode
      0x01 , 0x2C , 0x2D ,              \ Line inversion mode
    PWCTR1        , 3      ,            \ Power control, 3 args:
      0xA2 ,
      0x02 ,                            \ -4.6V
      0x84 ,                            \ AUTO mode
    PWCTR2        , 1      ,            \ Power control, 1 arg:
      0xC5 ,                            \ VGH25 = 2.4C VGSEL = -10 VGH = 3 * AVDD
    PWCTR3        , 2      ,            \ Power control, 2 args:
      0x0A ,                            \ Opamp current small
      0x00 ,                            \ Boost frequency
    PWCTR4        , 2      ,            \ Power control, 2 args:
      0x8A ,                            \ BCLK/2, Opamp current small & Medium low
      0x2A ,
    PWCTR5        , 2      ,            \ Power control, 2 args:
      0x8A , 0xEE ,
    VMCTR1        , 1      ,            \ Power control, 1 arg:
      0x0E ,
    MADCTL        , 1      ,            \ Memory access control (directions), 1 arg:
      0xC8 ,                            \ row addr/col addr, bottom to top refresh
    COLMOD        , 1      ,            \ set color mode, 1 arg:
      0x03 ,                            \ 12-bit color
    GMCTRP1       , 16      ,           \ Gamma + polarity Correction Characterstics
      0x02 , 0x1c , 0x07 , 0x12 ,
      0x37 , 0x32 , 0x29 , 0x2d ,
      0x29 , 0x25 , 0x2B , 0x39 ,
      0x00 , 0x01 , 0x03 , 0x10 ,
    GMCTRN1       , 16      ,           \ Gamma - polarity Correction Characterstics
      0x03 , 0x1d , 0x07 , 0x06 ,
      0x2E , 0x2C , 0x29 , 0x2D ,
      0x2E , 0x2E , 0x37 , 0x3F ,
      0x00 , 0x00 , 0x02 , 0x10 ,
    NORON         , 0       ,           \ Normal display on
    0 ,

:m clk  [ 2 .p1 set 2 .p1 clr ] m;
:m 1bit 2*' 1 .p1 movcb clk m;
:m /C/  [ 0 .p1 clr ] m;
:m /D/  [ 0 .p1 set ] m;

: (>st) 1bit 1bit 1bit 1bit
: _4    1bit 1bit 1bit 1bit 2*' ;
: (4>st) 2*' 2*' 2*' 2*' _4 ;
: 4>st  (4>st) drop ;

: write-cmd  ( b )   /C/
: 1>st       ( b )   1bit 1bit 1bit 1bit 1bit 1bit 1bit 1bit drop ;
: write-data ( b )   /D/ 1>st ;
: data16     ( b )   0# write-data write-data ;

: args
    begin
        0=if drop; then
        @p+ write-data
        1-
    again

: coldregs
    init-table ##p!
    begin
        @p+
        0=if drop; then
        write-cmd
        @p+
        dup $7f # and args
        -if @p+ ms then
        drop
    again

here [ $1000 > throw ]
$1000 org
: dim ( x w )
    over data16 + 1- data16 ;
: rect              ( x y w h )
    twist           ( x w y h )
    RASET # write-cmd dim
    CASET # write-cmd dim
: writing
    RAMWR # write-cmd
    /D/ 
;

: full
    blu #@ (4>st)
    grn (#@) (4>st) red (#@) 4>st ;

:m |4>st 1bit 1bit 1bit 1bit m;

: half 10 #
: gray
    0=if
        drop
: dark
        1 .p1 clr
        clk clk clk clk
        clk clk clk clk
        clk clk clk clk ;
    then
    5 (#!) [ blu b mov mul ] $f # + |4>st
    5 (#@) [ grn b mov mul ] $f # + |4>st
    5 (#@) [ red b mov mul ] $f # + |4>st drop ;

: ndark
    7 #for dark 7 #next ;

: cls       ( )
    0# 0# 128 # 160 #
    rect

    160 # 6 #for
        128 # ndark
    6 #next ;

: /st7735
    [ 3 .p1 clr ]
    1 # ms
    [ 3 .p1 set ]
    coldregs

    cls
: white
    $f #
: setgray
    red (#!) grn (#!) blu #! ; 
: black
    0# setgray ;

$1fff constant TOPMEM
947 here
include fontsize.fs
[ TOPMEM FONTDATA_SIZE - ] org
include font.fs
here TOPMEM <> throw
org 947 <> throw


:m 4.4r ( - l h )
    dup clra
    dup $93 , $a3 , \ |@p+
    xchd [swap] m;

: 4.4 ( - h l )
    4.4r swap ;

: skip
    4.4 * 1+ clrc 2/'
: +p
    [ dpl add ] dpl (#!)
    [ clra dph addc ] dph (#!)
    drop;

: seek ( c - ) \ p points to the data for character c
    font ##p!
    begin
        dup @p+ xor 0=if 2drop ; then
        drop skip
    again

: xy!   y #! x #! ;
: xy@   x #@ y #@ ;
: adv   x #+! ;            \ advance cursor

: preloop ( l h - i j )
    swap if 1u+ then ;

\ Fill rect with current color
: wash ( x y w h )
    2dup um* d1+ d2/ preloop 7 #! 6 #!
    rect
    begin begin
        full full
    7 #next 6 #next ;

: ch ( c - )
    p>r
    seek
    xy@
    4.4                     ( w h )
    over adv
    2dup * push             ( w h  r: w*h )
    rect
    pop 1+ 2/ 7 #for
        4.4r gray gray
    7 #next
    
    r>p ;

: blch
    black
    xy@ 8 # 9 # wash
    8 # adv white ;

: str
    @p+ 6 #for
        @p+
        ch
    6 #next ;

: setcolor
    4.4 grn #! red #! @p+ blu #! ;

: hex1 ( h - )
    x #@ 3 # + $7f # xor 4 #
    RASET # write-cmd dim

    RAMWR # write-cmd
    /D/

    micro ##p!
    $f # and 10 # b #! [ mul ] +p
    10 # 7 #for 4.4r gray gray 7 #next
    5 # x #+! ;

: drawhex ( hh - )
    y #@ 5 #
    CASET # write-cmd dim

    dup [swap] hex1 hex1 ;

:m gap [ y inc ] m;

: clip
    y #@
: (clip)
    -if
        $7f # and negate + ;
    then
    drop;

: preblank ( w )
    dup y #@ + (clip)
    dup push x #@ -4 # + y #@
    16 # pop rect
    6 #for 16 # ndark 6 #next ;

: bitmap
    0 #
: +bitmap ( o )
    x #@ + y #@
    -if 2drop ; then
    4.4                     ( w h )
:  (bitmap)                 ( x y w h )
    dup y #+!
    clip
    2dup * push             ( w h  r: w*h )
    rect
    pop 1+ clrc 2/' 7 #for
        4.4r gray gray
    7 #next ;

: (hex2)
    micro ##p!
    $f # and 10 # * +p
    y #@ -if drop; then drop
    x #@ 3 # + y #@
    5 # 4 #
    (bitmap) ;

: hex2 ( u - )
    dup (hex2)
    gap
    [swap] (hex2)
    ;

: acknak
    0=if'
        $c # red #!
        $2 # grn #!
        $2 # blu #! ;
    then
    $2 # red #!
    $c # grn #!
    $2 # blu #! ;

: d-byte-ack
    acknak
    18 # preblank
    gap
    dot ##p!
    7 # +bitmap

    gap

    white
    hex2
    gap gap gap ;

: barpoint ( u - ) \ update the slash bar bounds
    -if drop; then
    dup
    talk0 #@ umin talk0 #!
    talk1 #@ umax talk1 #! ;

: slashcolor 8 # setgray ;

here constant DRAW-SEGMENT  \ This block must all be in the same 2K segment

: startwave
    128 # 7 #!
    0 # 8 # 128 # rect
    story # a!
    [
     SP x mov
     x dec
     x dec
     0 y mov
    ] ;

: column
    $df cond
: bail
    [
     x SP mov
     y 0 mov
    ] then ;

: hi full dark dark dark dark dark dark dark column ;
: lo dark dark dark dark dark dark dark full column ;
: change
    full full full full full full full full column ;
: undef
    half half half half half half half half column ;

: d-stop
    drop a+
    0 # red #!
    7 # grn #!
    7 # blu #!
    symbol-p ##p!
: (d-stop)
    12 # preblank
    bitmap ;

:m y; \ return if y>127
    $bc , 128 , 0 ,     \ CJNE R4,#128,+0
    0=if' ; then m;

: d-direction
    arrow ##p!
    if'
        larrow ##p!
    then
    $f # red #!
    $e # grn #!
    $2 # blu #!
    -5 # y #+!
    bitmap ;

: slashv ( u - ) \ draw the bottom slash segment
    $08 # <if drop; then
    $78 # <if
        talked. 0=if.
            talker (#!)
            talked. set
        then
        talker @=if
            slashcolor
            x #@ -4 # + y #@ -5 # +
            dup $7f # xor barpoint
            6 # 1 # wash
        then
    then
    drop;

: d-start
    acknak
    18 # preblank
    gap
    dot ##p!
    7 # +bitmap
    drop @+ clrc 2/'

    d-direction

    gap

    dup white hex2
    slashv

    gap gap gap
    y;
    $c # red #!
    $8 # grn #!
    $0 # blu #!
    symbol-s ##p!
    (d-stop) ;

: d-byte
    drop @+ d-byte-ack ;

: d-bang
    drop a+
    15 # red #!
    0 # grn #!
    1 # blu #!
    symbol-b ##p!
    12 # preblank
    bitmap ;

: d-quit a+ 128 # y #! drop;
:m jumptable 2* here [ 4 + ] ##p! $73 , ( JMP @A+DPTR ) m;

: dispatch
    @+ jumptable
    ( 0 ) d-quit ;
    ( 1 ) d-stop ;
    ( 2 ) d-start ;
    ( 3 ) d-byte ;
    ( 4 ) d-bang ;

: l-dispatch
    begin
        dispatch
        y;
    again

:m pinkwash
    8 # red #!
    0 # grn #!
    8 # blu #!
    0 # 117 # 128 # 17 #
    wash m;

: hline ( x y l ) 1 # wash ;
: vline ( x y l ) 1 # swap wash ;

: addrgrid ( u - ) \ C set if column 7
    dup 2/ 2/ 2/ 7 # * 7 # + y #!
    7 # and dup 17 # * x #!
    -7 # + drop;

: (slash) ( u - ) \ from the address, vertical down line
    addrgrid
    [ y inc y inc ]
    0=if'
        10 # adv
        xy@ 3 # hline
        3 # adv
    else
        -4 # adv
        xy@ 3 # hline
    then

    xy@ 117 # over - vline ;

: slash ( u - )
    slashcolor (slash)
    [ x slashx mov ] ;

: unslash ( u - )
    black (slash) ;

: d-slashbar
    0# setgray                              \ undraw
    0# 117 # 128 # hline
    slashcolor
    talked. if.
        slashx #@ barpoint
        talk0 #@ talk1 #@ over negate + 1+
        117 # swap hline
    then ;

: ingrad ( u - )
    2* grad ##p! +p setcolor ;

: newtalker
    white
: d-addr
    dup addrgrid drawhex ;

: d-sda-stop
    5 # 6 #for hi 6 #next
    change 
    6 # 6 #for lo 6 #next
    prev. clr
    a+ drop;

: bar
    0=if'
        prev. if. change else lo then lo ;
    then
    prev. 0=if. change else hi then hi ;

: d-sda-byte
    @+
    cplc
    9 # 6 #for
        bar
        [ prev. movcb ]
        2/'
    6 #next
    drop drop;

: d-sda-start
    d-sda-byte
    6 # prev. if. change 1- then
    6 #for lo 6 #next
    change 
    5 # 6 #for hi 6 #next
    prev. set
    ;

: d-sda-none
    label-sda [ 1 + ] ##p!
: (label)
    16 # 1 #for
        4 # 6 #for
            4.4r gray gray
        6 #next
        column
    1 #next
    begin hi again

: d-sda-bang
    12 # 6 #for undef 6 #next
    a+ drop;

: sda-dispatch
    @+
    jumptable
    ( 0 ) d-sda-none ;
    ( 1 ) d-sda-stop ;
    ( 2 ) d-sda-start ;
    ( 3 ) d-sda-byte ;
    ( 4 ) d-sda-bang ;

: d-sda
    140 # startwave
    $4 # red #!
    $5 # grn #!
    $f # blu #!
    begin
        sda-dispatch
    again

: 9hi
    9 # 6 #for hi 6 #next ;
: 2lo
    2 # 6 #for lo 6 #next ;
: d-scl-stop
    9hi
    change 
    2lo
    a+ drop;

: d-scl-byte
    a+
    9 # 6 #for
        lo change
    6 #next
    drop;
: d-scl-start
    d-scl-byte
    2lo
    change 
    9hi
    ;

: d-scl-none
    label-scl [ 1 + ] ##p!
    (label) ;

: scl-dispatch
    @+ jumptable
    ( 0 ) d-scl-none ;
    ( 1 ) d-scl-stop ;
    ( 2 ) d-scl-start ;
    ( 3 ) d-scl-byte ;
    ( 4 ) d-sda-bang ;

here [ DRAW-SEGMENT xor $f800 and throw ]

: d-scl
    152 # startwave
    $c # red #!
    $b # grn #!
    $1 # blu #!
    begin
        scl-dispatch
    again

: rtl
    %10101000 #
: >madctl
    MADCTL # write-cmd write-data ;
: ltr
    %11001000 # >madctl ;

: drawmode
    black
    0# 0# 2dup 10 # 9 # wash
    white xy! mode #@ ch ;

: fixed
    rtl
    3 # setgray
    $08 #
    112 # 6 #for
        dup d-addr
        1+
    6 #next

    ltr

    drawmode

    tplan ##p!
    begin
        @p+ 0=if drop; then
        @p+ xy!
        setcolor
        str
    again

:  d-slash
    talked. if.
        ptalked. if.
            ptalker #@ talker @=if drop; then
            unslash
        then
        talker #@ slash ;
    then
    ptalker #@ unslash ;

: cool1 ( addr - )
    \ talker @=if talked. if. drop; then then
    dup heatmap @x if  ( addr h )
        1- (!x) ingrad
        d-addr ;
    then
    2drop ;

: cool
    rtl
    $08 #
    112 # 6 #for
        dup cool1
        1+
    6 #next
    drop
    ltr ;

\ talked. is true when talker is valid
\ ptalked. and ptalker hold previous values
\ slashx is set to the X of the slash line

: waves
    \ pinkwash

    rtl

    122 # 0 # xy!

    $ff # talk0 #!
    $00 # talk1 #!
    talked. clr

    story # a!
    l-dispatch

    d-sda
    d-scl

    ltr

    d-slash
    d-slashbar

    talker #@ ptalker #!
    [ talked. movbc ptalked. movcb ]

    DISPON # write-cmd
    ;
