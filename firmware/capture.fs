
here constant CAPTURE-START

[
: fake ( a - u )
    dup 0= ] here [ and or ;
]

:m ::  (  - )
	[ >in @ label >in !
	create ] here [ , hide 
	does> @ ] m;

\ jump if bit is 0 or 1 ( addr bit )
:m j1 ( addr bit ) [ swap fake swap ] 0=until. m;
:m j0 ( addr bit ) [ swap fake swap ] until. m;
:m j  ( addr )     fake again m;

:m tx SBUF0 (#!) clra TMR3H (#!) m;
:m SDA0 ( a ) SDA j0 m;
:m SDA1 ( a ) SDA j1 m;

fwd L00.0
fwd L00.1
fwd L00.2
fwd H00.0
fwd H00.1
fwd H00.2
fwd HS
fwd HP
fwd LP
fwd LS

:m escape   RI0 if. RI0 clr ; then m;

:: L11      begin LS    SDA0 SCL 0=until.
:: Lidle    begin begin SDA until. SCL until.
            L11 j

:: L10.0    3 .t set
            begin L00.0 SDA0 SCL until.  begin LS SDA0 SCL 0=until. 2 .t set
:: L10.1    begin L00.1 SDA0 SCL until.  begin LS SDA0 SCL 0=until. 1 .t set
:: L10.2    begin L00.2 SDA0 SCL until.  begin LS SDA0 SCL 0=until. 0 .t set
            tx
:: H10.0    7 .t set
:: klak     begin H00.0 SDA0 SCL until.  begin HS SDA0 SCL 0=until. 6 .t set
:: H10.1    begin H00.1 SDA0 SCL until.  begin HS SDA0 SCL 0=until. 5 .t set
:: H10.2    begin H00.2 SDA0 SCL until.  begin HS SDA0 SCL 0=until. 4 .t set
            L10.0 j

:: LS       $f0 # and $01 # ior tx      ( start )
:: LS2      begin HP    SDA1 SCL 0=until.
            H00.0 j

:: HS       $10 (#)                     ( start )
:: HS2      begin LP    SDA1 SCL 0=until.
:: L00.0    3 .t set
            begin L10.0 SDA1 SCL until.  begin LP SDA1 SCL 0=until.
:: L00.1    begin L10.1 SDA1 SCL until.  begin LP SDA1 SCL 0=until.
:: L00.2    begin L10.2 SDA1 SCL until.  begin LP SDA1 SCL 0=until.
            tx
:: H00.0    7 .t set
            begin H10.0 SDA1 SCL until.  begin HP SDA1 SCL 0=until.
:: H00.1    begin H10.1 SDA1 SCL until.  begin HP SDA1 SCL 0=until.
:: H00.2    begin H10.2 SDA1 SCL until.  begin HP SDA1 SCL 0=until.
            L00.0 j

:: HP       $20 (#)
            \ L11 j
            begin SDA 0=until.
            escape
            HS2 j

: (warm)
:: H11      begin HS    SDA0 SCL 0=until.
:: Hidle    begin begin SDA until. SCL until.
            H11 j

:: LP       $f0 # and $02 # ior tx
            \ H11 j
            begin SDA 0=until.
            escape
            LS2 j

: /timer3
    $80 # EIE1 ior!             \ Timer 3 interrupt enable
;
: timer3\
    $80 ~# EIE1 and!            \ Timer 3 interrupt disable
;

:m timer3
    SBUF0 (#!) clra
    $7f # TMR3CN and!
    RI0 if.
        RI0 clr
        [ sp dec ]
        [ sp dec ]
    then
    [ reti ] m;

: capture
    [ IE push ]
    [ ET2 clr ]                 \ Timer 2 interrupt disable
    [ ES0 clr ]                 \ UART interrupt disable
    \i2chw

    [ clra ]
    [ FL1 set ] t3+
    (warm)
    t3- [ FL1 clr ]
    /i2chw
    [ IE pop ]
    ;

\ This code all runs in register bank 1:
\   0   scratch for heatmap
\   1   log
\   2   
\   3   prev cmd
\   4   constant 72, for heatmap
\   5
\   6
\   7   caller acc save
\
\ FL0 set means this is an address byte

fwd M00.0
fwd M10.0
fwd M10.1
fwd M10.2
fwd M10.3
fwd M10.4
fwd M10.5
fwd M10.6
fwd M10.7
fwd M10.8
fwd Mt
fwd MP

:m (l!) $f3 , m;

:m (log!)
    $f3 , a+ m;

:m wrap
    $7f # 9 and! m;

:m heat
    \ byte is in t
    FL0 if.
        setc 2/'
        0 (#!)
        4 (#@) $f2 ,
    then
m;

:m escape
    7 (#@)
    [
    dirty set
    PSW pop
    reti
    ]
m;

:: MP
            $00 (#) (log!)
            $01 (#) (log!)
            wrap
            escape
            begin SDA 0=until.
: (mismatch)
:: Mt
            begin MP    SDA1 SCL 0=until.
            $82 # 3 #! FL0 set
            M00.0 j

:: M00.6    begin M10.6 SDA1 SCL until.  begin MP SDA1 SCL 0=until.
:: M00.7    begin M10.7 SDA1 SCL until.  begin MP SDA1 SCL 0=until.         (l!)
:: M00.8    begin M10.8 SDA1 SCL until.  begin MP SDA1 SCL 0=until.         heat
            a+ 3 (#@) (l!) a+ wrap
            $83 # 3 #! FL0 clr
            M00.0 j

:: M10.6    begin M00.6 SDA0 SCL until.  begin Mt SDA0 SCL 0=until. 1 .t set
:: M10.7    begin M00.7 SDA0 SCL until.  begin Mt SDA0 SCL 0=until. 1+       (l!)
:: M10.8    begin M00.8 SDA0 SCL until.  begin Mt SDA0 SCL 0=until.
            a+ 3 (#@) $7f # and (l!) a+ wrap
            $83 # 3 #! FL0 clr
            M10.0 j

:: MP3      MP j
:: Mt3      Mt j
:: M00.3    begin M10.3 SDA1 SCL until.  begin MP3 SDA1 SCL 0=until.
:: M00.4    begin M10.4 SDA1 SCL until.  begin MP3 SDA1 SCL 0=until.
:: M00.5    begin M10.5 SDA1 SCL until.  begin MP3 SDA1 SCL 0=until.
            M00.6 j
:: M10.3    begin M00.3 SDA0 SCL until.  begin Mt3 SDA0 SCL 0=until. 4 .t set
:: M10.4    begin M00.4 SDA0 SCL until.  begin Mt3 SDA0 SCL 0=until. 3 .t set
:: M10.5    begin M00.5 SDA0 SCL until.  begin Mt3 SDA0 SCL 0=until. 2 .t set
            M10.6 j

:: MP0      MP j
:: Mt0      Mt j

: (warm)
:: M00.0    clra
            begin M10.0 SDA1 SCL until.  begin MP0 SDA1 SCL 0=until.
:: M00.1    begin M10.1 SDA1 SCL until.  begin MP0 SDA1 SCL 0=until.
:: M00.2    begin M10.2 SDA1 SCL until.  begin MP0 SDA1 SCL 0=until.
            M00.3 j
:: M10.0    clra
            begin M00.0 SDA0 SCL until.  begin Mt0 SDA0 SCL 0=until. 7 .t set
:: M10.1    begin M00.1 SDA0 SCL until.  begin Mt0 SDA0 SCL 0=until. 6 .t set
:: M10.2    begin M00.2 SDA0 SCL until.  begin Mt0 SDA0 SCL 0=until. 5 .t set
            M10.3 j

: /monitor
    [ ET2 clr ]                 \ Timer 2 interrupt disable
    [ ES0 clr ]                 \ UART interrupt disable
    \i2chw
    t3i- t3+                    \ Timer3 running, no intr

    %00000100 # P0MASK #!
    %00000100 # P0MAT #!        \ SDA high

    %00010000 # P1MASK #!
    %00010000 # P1MAT #!        \ SCL high

                                \ constants in registers
    72 # [ 4 8 + ] #!
    $02 # EIE1 ior!             \ EMAT
    ;

: \monitor
    $02 ~# EIE1 and!            \ EMAT off
    [ ET2 set ]                 \ Timer 2 interrupt enable
    [ ES0 set ]                 \ UART interrupt enable
    t3i+ t3-                    \ Timer3 stopped, intr
    /i2chw
    ;

:m mismatch
    [
    PSW push
    RS0 set
    ]
    7 (#!)
    Mt j
m;

here [
CAPTURE-START xor 11 rshift 0<>
[IF]
cr .( Capture block cannot cross a 2K boundary)
abort
[THEN]
]
