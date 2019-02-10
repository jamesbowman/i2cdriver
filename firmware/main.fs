24500000 constant SYSCLK

0 constant CLOSEUP

\ P0.0  SDA 2K2
\ P0.1  SDA 4K3
\ P0.2  SDA
\ P0.3  SDA 4K7
\ P0.4  RX
\ P0.5  TX
\ P0.6  A.V
\ P0.7  A.C

\ P1.0  RS/DC
\ P1.1  DATA
\ P1.2  CLOCK
\ P1.3  RESET
\ P1.4  SCL
\ P1.5  SCL 2K2
\ P1.6  SCL 4K3

\ P2.0  SCL 4K7

0 [if]
There are 3 threads:

         1000Hz tick. Increments the BCD milliscond timer.
         Timer 2 interrupt.

         UART/SPI service. Runs the transport.
         UART and SPI interrupts.
         [DPTR, R0]

         graphics. renders the main image.
         Main thread.
         [DPTR, R0-7]
         ADC drive. Runs ADC conversions, stores results in adc-.
         ADC end of conversion interrupt.

[then]
[ : ," '"' parse dup ] , [
    bounds do
        i c@ ] , [
    loop
;
]

:m t3+  %00000100 # TMR3CN #! m;    \ Timer 3 enable
:m t3-  %00000000 # TMR3CN #! m;    \ Timer 3 enable
:m t3i+ $80 # EIE1 ior! m;  \ Timer 3 interrupt enable
:m t3i- $80 ~# EIE1 and! m; \ Timer 3 interrupt disable

$0090 org
: 2dup  |over
: over  |over ;
: tuck  swap over ;
:m p>r  [ dpl push dph push ] m;
: r>p   [ dph pop  dpl pop ] ;  \ MUST be followed by ;
: @p    |@p ;
: @p+   |@p+ ;
: *     |* ;
: um*   |um* ;
:m #+! [ dup add ] #! m;
: dnegate
    swap invert swap invert
: d1+ 
    swap 1 # + swap 0 # +' ;
: d+	push swap push + pop pop +' ;
:m d2/  clrc 2/' swap 2/' swap m;
: - negate + ;

: twist ( a b c d -- a c b d )
    push swap pop ;

:m /uart
    REN0 set                    \ Receive enable

    TR1 set
    $20 # TMOD #!
    $18 # CKCON #!              \ Use system clock (T1,T2)
    [ SYSCLK 2/ 1000000 / negate ] #
    TH1 #!                      \ speed
    ES0 set
m;

[ : array create , does> @ + ; ]

$10 cpuORG

$09 constant log                    \ logging ring pointer

cpuHERE constant tempr 2 cpuALLOT   \ temperature ADC
cpuHERE constant currr 2 cpuALLOT   \ current ADC
cpuHERE constant currd 2 cpuALLOT   \             decimal
cpuHERE constant slowc 1 cpuALLOT   \ slow refresh counter
cpuHERE constant charc 1 cpuALLOT   \ character counter
cpuHERE constant convs 1 cpuALLOT   \ converter state (2 bit)
cpuHERE constant other 1 cpuALLOT   \ context SP save
cpuHERE    array clock 6 cpuALLOT

cpuHERE $20 <> throw

cpuHERE constant flags  1 cpuALLOT          $00 constant dirty
                                            $01 constant prev.
                                            $02 constant talked.
                                            $03 constant ptalked.
                                            $04 constant fade.
                                            $05 constant risen.
                                            $06 constant modechange.
                                            $07 constant timeout
cpuHERE constant ftemp  1 cpuALLOT          $08 constant f.0
                                            $09 constant f.1
                                            $0a constant f.2
                                            $0b constant f.3
                                            $0c constant f.4
                                            $0d constant f.5
                                            $0e constant f.6
                                            $0f constant f.7
cpuHERE constant flags2 1 cpuALLOT          $10 constant weighing

cpuHERE constant mode   1 cpuALLOT
cpuHERE constant tempd  2 cpuALLOT          \             decimal
cpuHERE constant vbusr  2 cpuALLOT          \ voltage ADC
cpuHERE constant vbusd  2 cpuALLOT          \             decimal

cpuHERE constant talk0  1 cpuALLOT
cpuHERE constant talk1  1 cpuALLOT
cpuHERE constant talker 1 cpuALLOT
cpuHERE constant ptalker 1 cpuALLOT
cpuHERE constant slashx 1 cpuALLOT
cpuHERE constant story  16 cpuALLOT
cpuHERE constant guard  2  cpuALLOT

[
cpuHERE constant red 1 cpuALLOT
cpuHERE constant grn 1 cpuALLOT
cpuHERE constant blu 1 cpuALLOT
]
3 constant x                        \ graphics x coordinate
4 constant y                        \ graphics y coordinate
cpuHERE constant i2cb 64 cpuALLOT

cr .( RAM used ) cpuHERE . .( bytes )

: swapctx [
    0 push
    1 push
    t push
    psw push
    dph push
    dpl push
    ]
    SP (#@)
    [ other xch ]
    SP (#!)
    [
    dpl pop
    dph pop
    psw pop
    t pop
    1 pop
    0 pop
    ]
    ;

: 0#    dup [ clra ] ;
: key   begin TI0 clr RI0 0=while. swapctx repeat RI0 clr SBUF0 #@ ;        \ XXX compare with spidriver
: emit  SBUF0 (#!) begin swapctx RI0 clr TI0 until. TI0 clr [ charc dec ]
: _drop drop ;

:m drop; _drop ; m;

: umax
    clrc $96 , $26 ,    \ C set if u>t
    if' drop; then nip ;
: umin
    clrc $96 , $26 ,    \ C set if u>t
    0=if' drop; then nip ;

: depth S #@ invert ;
0 [if]
include debug.fs
[then]
: 1ms
    1 #
: ms
    slowc (#!)
    begin slowc (#@) 0=until drop;

: 5µs
	5 #
: µs
    1 #for
        nop nop nop nop
        nop nop nop nop
    1 #next
    ;

\ ---------------------------------------- DECIMAL
5 constant d.l          \ decimal accumulator
6 constant d.h

: decimal ( u. -- d. )   \ d is the BCD of u
    0 # d.l #!
    0 # d.h #!
    16 # 7 #for
        swap 2*' swap 2*'
        d.l #@ [ d.l addc da ] d.l #!
        d.h #@ [ d.h addc da ] d.h #!
    7 #next
    2drop d.l #@ d.h #@ ;

: 10trunc
    swap $f0 # and swap ;
: 5trunc
    swap
    dup $f # and 5 # <if
        0#
    else
        5 #
    then
    push xor pop + swap ;

: fold  ( d. -- )           \ Add d to [4 5 6]
        swap
        5 #+!
        [ 6 addc ] 6 #!
        if' [ 7 inc ] then ;

: (uq*)  ( a. b. -- q.. )
                            \ 4     5    6    7
        4 #2!               \ bl    bh
        7 #!                \                 ah
        6 (#!)              \            al

             5 #@ um*       \ m16 = 5 * 6
        4 #@ 7 #@ um*       \ m16 = 4 * 7

        5 #@ 7 #@ um*       \ hi16
        4 #@ 6 #@ um*       \ lo16

                            \ 4     5    6    7
                            \ LSB           MSB
        5 #! 4 #! 7 #! 6 #!
        fold fold ;

: uq*   (uq*) 4 #2@
: 67@   6 #2@ ;
: h*    (uq*) 67@ ;

\ ---------------------------------------- Analog thread
:m /adc
    AD0EN set
    BURSTEN set
    5 # ADC0AC #!               \ accumulate 64 samples
    0 # ADC0CN1 #!              \ common mode buffer disabled
    %00011100 # REF0CN #!       \ temp sensor on, 1.65 V ref
    $40 # ADC0PWR #!
    \ $BF # ADC0TK #!
    m;

:m 1.65v %11111001 # ADC0CF #! m; \ PGA gain is 1
:m 3.3v  %11111000 # ADC0CF #! m; \ PGA gain is 0.5
:m startconv
    AD0BUSY set m;

:m 2move [ over 1+ over 1+ mov mov ] m;

\ Exponential Moving Average, alpha is 1/8

: alpha d2/ d2/ d2/ ;

: ema ( addr -- )
    (a!) (@+) @
    2dup alpha dnegate d+
    ADC0L #2@ alpha d+
    !- !
    ;

: converter ( u - u )
    weighing if.
        weighing clr
        $ff (#) ;
    then
    -if ; then

    0 # =if
        currr # ema
        %10000 # ADC0MX #!          \ mux temperature
        1.65v startconv 1+ ; then
    1 # =if
        tempr # ema
        %00110 # ADC0MX #!          \ mux P0.6
        3.3v startconv 1+ ; then
    vbusr # ema
: /converter
    %00111 # ADC0MX #!          \ mux P0.7
    startconv [ clra ] ;

[
: converts ( val adc ) $10000 swap */ constant ;
]

\ include cal-b3.fs
\ include cal-DO00N2O5.fs
\ include cal-DO00N1GI.fs
include cal.fs

: conversions
    vbusr #2@ voltage ## h*
    decimal vbusd #2!
    tempr #2@ kel ## h* celsius ## d+
    decimal tempd #2!
    currr #2@
    0current [ 1 max negate ] ## d+ 0=if' 2drop 0 ## then
    current ## h*
    decimal 5trunc currd #2!
;

\ ---------------------------------------- I2C

2 .p0 constant SDA
4 .p1 constant SCL

[ 256 SYSCLK 100000 3 * / - ] constant I2C_100
[ 256 SYSCLK 400000 3 * / - ] constant I2C_400

:m /i2chw %11011000 # SMB0CF #! m; \ Enable, no slave, use T0, EXTHOLD, SCL timeouts
:m \i2chw %00000000 # SMB0CF #! m;

: /i2c
    $04 # CKCON ior!        \ T0 use system clock
    $02 # TMOD ior!         \ T0 in 8-bit auto-reload

    /i2chw
    $01 # SMB0ADM #!        \ EHACK=1
    $04 # XBR0 ior!
: 100Khz
    I2C_100 # TH0 #!
    TR0 set ;
: 400Khz
    I2C_400 # TH0 #!
    TR0 set ;

:m (>crc) CRC0IN (#!) m;

: hdigit
    dup
: (hdigit)
    [swap]
: digit
    $f # and
    -10 # + -if -39 # + then 97 # + emit ;
: dd     hdigit digit ;

: >i2c
    MASTER 0=if. drop; then
    (>crc)
    SMB0DAT #!
: i2c
    [ SI clr ]
: (i2c)
    [ timeout clr ]
: i2c-wait
    $01 # EIE1 ior!             \ ESMB0 
    t3+
    begin swapctx SI until.
    t3-
    $01 ~# EIE1 and!            \ ESMB0 
    ;
: i2c-start
    [ STA set ]
    i2c
    [ STA clr ] ;
: i2c-stop
    [ STO set SI clr ] ;
: i2c>
    MASTER 0=if. $ff # ; then
	i2c SMB0DAT #@ (>crc) ;

: i2c-leave
    SMB0CF #@
    7 .t 0=if. drop; then       \ already turned off
    5 .t if.  i2c-stop 10 # µs then
    \i2chw
    $04 ~# XBR0 and! drop;

: setport ( u )     \ SCL SCL_DIR SDA SDA_DIR

    P0MDOUT ftemp mov
    2/' f.2 movcb
    ftemp P0MDOUT mov
    2/' P0.2 movcb
    P1MDOUT ftemp mov
    2/' f.4 movcb
    ftemp P1MDOUT mov
    2/' P1.4 movcb ;

: i2c-restore
    %1010 # setport drop
    /i2chw
    $04 # XBR0 ior! ;

: i2c-reset
    i2c-leave
	[ SDA set SCL clr ]
	10 # 2 #for
		[ SCL set ] 5µs
		[ SCL clr ] 5µs
	2 #next
	\ a STOP signal (SDA from low to high while CLK is high)
	[ SDA clr ] 5µs
	[ SCL set ] 2 # µs
	[ SDA set ] 2 # µs
    i2c-restore
    STO clr ;

: bitbang
    i2c-leave
    begin
        key
        '@' # =if drop; then
        setport
        
        2/' if'
            0#
            P1.4 movbc 2*'
            P0.2 movbc 2*'
            emit
        then
        drop
    again

: doconv
    startconv
    begin AD0INT until. AD0INT clr ;
: measure ( - )    \
    doconv
    ADC0H #@ emit ;

: startweigh ( u )
    weighing set
    i2c-leave
    [ SCL set SDA set ]
    %00000100 ~# P0MDIN and!
    %00010000 ~# P1MDIN and!
: pulldir ( u ) [ \ Set pullup/down direction (1=up, 0=down)
    2/' P0.0 movcb
    2/' P0.1 movcb
    2/' P0.3 movcb
    2/' P1.5 movcb
    2/' P1.6 movcb
    2/' P2.0 movcb
    ] drop;

: weigh
    0# [ weighing movbc ] 2*'          \ 1=pending, 0=ready
    dup emit
    0=if
        0# µs

        3.3v
        %0010 # ADC0MX #! measure
        %1100 # ADC0MX #! measure

        %00000100 # P0MDIN ior!
        %00010000 # P1MDIN ior!

        dup /converter convs #!
        %111111 # pulldir
        i2c-restore
    then drop;

\ ---------------------------------------- timer service

: timer2
    [ psw push t push ]
    [
    slowc dec
    setc
    clra 0 clock dup addc da (#!)
    clra 1 clock dup addc da (#!)
    clra 2 clock dup addc da (#!)
    clra 3 clock dup addc da (#!)
    clra 4 clock dup addc da (#!)
    clra 5 clock dup addc da (#!)
    ] [ t pop psw pop ] ;

: timer3a
    \i2chw
    timeout set
    SI set
    /i2chw
    [ reti ]


\ ---------------------------------------- CRC16
:m /crc
    %1100 # CRC0CN0 #!
    m;

:m crc16
    CRC0DAT #@
    CRC0DAT #@ m;

\ ---------------------------------------- pullups

\ P0.0  SDA 2K2
\ P0.1  SDA 4K3
\ P0.2  SDA
\ P0.3  SDA 4K7

\ P1.4  SCL
\ P1.5  SCL 2K2
\ P1.6  SCL 4K3

\ P2.0  SCL 4K7

: SDA_2k2   %00000001 # P0MDOUT ior! ;
: SDA_4k3   %00000010 # P0MDOUT ior! ;
: SDA_4k7   %00001000 # P0MDOUT ior! ;

: SCL_2k2   %00100000 # P1MDOUT ior! ;
: SCL_4k3   %01000000 # P1MDOUT ior! ;
: SCL_4k7   %00000001 # P2MDOUT ior! ;

\   5       4       3       2       1       0
\   SCL_4k7 SCL_4k3 SCL_2k2 SDA_4k7 SDA_4k3 SDA_2k2
: pull@ ( - u )
    0# [
    P2MDOUT ftemp mov
    f.0 movbc 2*'
    P1MDOUT ftemp mov
    f.6 movbc 2*'
    f.5 movbc 2*'
    P0MDOUT ftemp mov
    f.3 movbc 2*'
    f.1 movbc 2*'
    f.0 movbc 2*' ] ;
: pull! ( u ) [
    P0MDOUT ftemp mov
    2/' f.0 movcb
    2/' f.1 movcb
    2/' f.3 movcb
    ftemp P0MDOUT mov
    P1MDOUT ftemp mov
    2/' f.5 movcb
    2/' f.6 movcb
    ftemp P1MDOUT mov
    P2MDOUT ftemp mov
    2/' f.0 movcb
    ftemp P2MDOUT mov
    ] drop;

: release
    %00001011 ~# P0MDOUT and!
    %01100000 ~# P1MDOUT and!
    %00000001 ~# P2MDOUT and!
;
: weak
    release
    %00001000 # P0MDOUT ior!
    %00000001 # P2MDOUT ior!
    ;
    
here constant "devname ," i2cdriver1"

: heatmap ( u - ) \ heatmap address in x
    $80 # + dpl #! ;

: ishot ( u )
    heatmap 72 # !x ;

: snap
    [ log dpl mov ]
    story # a!
    dup
    16 # 7 #for
        [ dpl dec ]
        $7f # dpl and!
        (@x)
        (!+)
    7 #next
    drop;

: type
    @p+ 2 #for @p+ emit 2 #next ;

: hdigit
    dup
: (hdigit)
    [swap]
: digit
    $f # and
    -10 # + -if -39 # + then 97 # + emit ;
: dd     hdigit digit ;
: dh.    dd
: h.     dd
: space
    32 # emit ;
: point
    '.' # emit ;
: d.d
    hdigit point digit ;

: .'   \ print carry
    [ '0' 2/ ] # 2*'
: emit_
    emit space ;

: i2c-speed
    TH0 #@
    I2C_400 # =if 4 (#) ; then
    1 (#) ;

: modechar
    'I' #
    SMB0CF ftemp mov
    f.7 if. ; then
    'B' (#) ;

: bracket
    79 # charc #!
    '[' # emit ;
: info
    bracket
    "devname ##p! type space
    "serial  ##p! type space

    5 clock #@ dd
    4 clock #@ dd
    3 clock #@ dd
    2 clock #@ dd
    1 clock #@ (hdigit)
    space

    vbusd #2@ d.d dd space
    currd #2@ digit dd space
    tempd #2@ digit d.d space

    modechar emit_

    [ SDA movbc ] .'
    [ SCL movbc ] .'

    i2c-speed digit $00 # dd space

    pull@ dd space

    crc16 dd dd
: pad
    charc #@ begin
        space 1-
    0=until
    drop
    ']' # emit
    ;

: introspect
    bracket

    $93 # h.
    0 #@ h.
    SP #@ h.
    SMB0CF #@ h.
    SMB0CN #@ h.
    TMR2L #2@ dh.
    TMR3L #2@ dh.
    IE #@ h.
    EIE1 #@ h.

    P0 #@ h.  P0MDIN #@ h.  P0MDOUT #@ h.
    P1 #@ h.  P1MDIN #@ h.  P1MDOUT #@ h.
    P2 #@ h.                P2MDOUT #@ h.

    convs #@ h.

    pad ;

\ Commands are:
\   e       echo next byte
\   s       select
\   u       unselect
\   80-bf   read 1-64 bytes
\   c0-ff   write 1-64 bytes

: count ( u -- u)
    63 # and 1+ ;

CLOSEUP [IF]
:m acmd                     \ Copy ACK into T.7 for a command byte
    [ 7 .t set ] m;
[ELSE]
:m acmd                     \ Copy ACK into T.7 for a command byte
    [ ACK movbc 7 .t movcb ] m;
[THEN]

: b>log ( arg - arg )
    3 # acmd over 
: >log ( cmd arg )
    [ dirty set ]
    [ log dpl mov   ]
    !x+ !x+
    $7f # dpl and!
    [ dpl log mov   ]
    ;

: alert ( u )
    [ timeout set ]
    drop 4 # 0 # >log ;

: rdN ( n -- )
    [ ACK set ]
    2 #for
        [ $b8 2 + ] , [ 1 cond ]    \ Clear ACK on final byte when R2 is 1
            [ ACK clr ]
        then
        i2c>
        (>crc) b>log emit
    2 #next ;

: rdNA ( n -- ) \ don't NACK final byte
    [ ACK set ]
    2 #for
        i2c> b>log emit
    2 #next ;

: report
    [ '0' 2/ 2/ 2/ ] #
    [ ARBLOST movbc ] 2*'
    [ timeout movbc ] 2*'
    [ ACK movbc ] 2*' emit ;

: flame ( u - u )
    dup clrc 2/' ishot ;

: do-start
    key
: log-start ( u )
    SDA 0=if. alert ; then
    i2c-start
    dup >i2c
    timeout if. alert ; then
    ACK if.
        flame
    then
    2 # acmd
    swap >log ;

: log-stop
    1 # 0# >log i2c-stop ;

: i2c-regrd \ expect (dev, reg, len)
    key 2* key key push     ( dev reg   R: len )
    over log-start          \ S/W
    b>log >i2c              \ reg
    1+ log-start            \ S/R
    pop rdN
    log-stop ;

: dmode
    'D' #
: newmode
    mode #! modechange. set ;

here constant WIP
: device-scan
    8 #
    112 # 2 #for
        i2c-start dup 2* >i2c
        ACK if. dup ishot then
        report
        i2c-stop
        1+
    2 #next drop ;

: service
    key
    -if
        6 .t if.
            count dup
            i2cb # a!  2 #for
                key
                b>log
                !+
            2 #next
            i2cb # a!  2 #for
                @+ >i2c
            2 #next
            report
            ;
        then
        count rdN ;
    then
    '?' # =if  info     then
    '1' # =if  100Khz then
    '4' # =if  400Khz then
    'a' # =if  key rdNA then
    'b' # =if  bitbang then
    'c' # =if  'C' # newmode then
    'd' # =if  device-scan then
    'e' # =if  key emit then
    'f' # =if  fade. set 'X' # emit then
    '_' # =if  $10 # RSTSRC #! then
    'i' # =if  i2c-restore then
    'm' # =if  'M' # newmode then
    'p' # =if  log-stop then
    'r' # =if  i2c-regrd then
    's' # =if  do-start report then
    'u' # =if  key pull! then
    'v' # =if  key startweigh then
    'w' # =if  weigh then
    'x' # =if
        i2c-reset
        [ '0' 2/ 2/ ] #
        [ SDA movbc ] 2*'
        [ SCL movbc ] 2*'
        emit
        then
    'J' # =if  introspect then
    drop ;

: thread2
    0 # 2 #for
        0# !x+
    2 #next
    \ '@' # emit
    begin
        service
    again ;

here constant _cap
[ : fwd 0 constant ; ]
include capture.fs
_cap org
[ : fwd bl word find 0= throw execute 0= throw ; ]
include capture.fs

0 constant Y_V
29 constant X_V
80 constant X_MA

include st7735.fs

: hdigit dup [swap]
: digit $f # and '0' # + ch ;
: dd     hdigit digit ;
: d3 ( d. )                         \ 3-digit space padded
    if digit dd ; then              \ ###
    drop blch
    10 # <if blch digit ; then      \ __#
    dd ;                            \ _##
: results
    white
    X_V  # Y_V # xy! vbusd #2@ hdigit '.' # ch digit hdigit drop
    X_MA # Y_V # xy! currd #2@ d3 ;


cpuHERE $80 max constant STACKS

: go
    $de # WDTCN #!
    $ad # WDTCN #!

    $01 # XBR0 #!
    $00 # XBR1 #!
    $c0 # XBR2 #!

    $00 # CLKSEL #!

    \ Clear RAM
    $08 # a!
    [ $100 $08 - ] # 7 #for 0 # !+ 7 #next

    $c0 SP! STACKS RP!
    [ ' thread2 >body @ ] ##p!
    [
    dpl push
    dph push
    0 push
    ]
    [ STACKS 8 + ] # other #!

    $100 SP! $c0 RP!

    %11001011 # P0SKIP #!       \ TX,RX,SDA
    %00010000 # P0MDOUT #!      \ 
    %00111111 # P0MDIN #!       \ analog P0.6 P0.7

    %11101111 # P1SKIP #!       \ SCL
    %00001111 # P1MDOUT #!
    /uart
    /adc
    /crc

    [ ticks/ms negate          ] # TMR2RLL #!
    [ ticks/ms negate 8 rshift ] # TMR2RLH #!

    dmode

    [ ET2 set ]                 \ Timer 2 interrupt enable
    [ TR2 set ]                 \ Timer 2 enable
    [ EA set ]
    t3i+

    release
    weak
    \ SDA_2k2
    \ SDA_4k3
    \ SDA_4k7

    \ SCL_2k2
    \ SCL_4k3
    \ SCL_4k7

    /i2c 100Khz

    [ dirty set ]
    swapctx

    /st7735 fixed
    25 # slowc #!

    /converter

    begin
        conversions

        dirty if.
            snap
            [ dirty clr ]
            waves
        then
        AD0INT if.
            AD0INT clr
            convs #@ converter convs #!
        then
        modechange. if.
            [ modechange. clr ]
            drawmode
            mode #@
            'C' # =if
                capture
                dmode
            then
            'M' # =if
                /monitor
            then
            drop
        then

        mode #@
        'M' # =if
            TMR3CN #@ -if
                $7f # TMR3CN and!
                cool
            then drop
            RI0 if.
                RI0 clr
                \monitor
                dmode
            then
        then
        drop

        slowc #@                \ 4 Hz
        0=if
            results
        then
CLOSEUP [IF]
        fade. if.
            cool [ fade. clr ]
        then
[ELSE]
        $1f # and 0=if          \ 32 Hz
            cool
        then
[THEN]
        drop
    again
here

\ Reset
$000 org go ;

\ UART interrupt
$023 org
    swapctx [ reti ]

\ Timer 2 overflow
$02b org [
    ] timer2 [
    TF2H clr
    reti
]

\ I2C
$03b org
    swapctx [ reti ]

\ Port mismatch
$043 org
    mismatch

\ Timer 3 overflow
$073 org
    FL1 if. timer3 then
    timer3a ;

org
