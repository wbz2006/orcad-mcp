# prep_ic_loaded.tcl — 参数化切换到某 IC 档带载态 (迭代用)
# 用法: 在 MCP tcl_eval 里先 set icargs {rb1 73k vampl 10.5m} 再 source 本文件
set st [DboState]
set pg [GetActivePage]
set out {}
if { ![info exists icargs] } { set icargs {rb1 73k vampl 10.5m} }
array set A $icargs
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set rn "?"
        catch { set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }
        if { $rn == "RL" } {
            catch { $pl SetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] [DboTclHelper_sMakeCString "2k"] }
            set cv [DboTclHelper_sMakeCString]
            catch { $pl GetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] $cv }
            lappend out "RL=[DboTclHelper_sGetConstCharPtr $cv]"
        }
        if { $rn == "Rb1" && [info exists A(rb1)] } {
            catch { $pl SetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] [DboTclHelper_sMakeCString $A(rb1)] }
            set cv [DboTclHelper_sMakeCString]
            catch { $pl GetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] $cv }
            lappend out "Rb1=[DboTclHelper_sGetConstCharPtr $cv]"
        }
        if { $rn == "Vs" && [info exists A(vampl)] } {
            catch { $pl SetEffectivePropStringValue [DboTclHelper_sMakeCString "VAMPL"] [DboTclHelper_sMakeCString $A(vampl)] }
            set cv [DboTclHelper_sMakeCString]
            catch { $pl GetEffectivePropStringValue [DboTclHelper_sMakeCString "VAMPL"] $cv }
            lappend out "VAMPL=[DboTclHelper_sGetConstCharPtr $cv]"
        }
    }
    set i [$it NextPartInst $st]
}
delete_DboPagePartInstsIter $it
# 别名统一: 输出节点别名设为 $A(alias) (默认 Vo)
if { ![info exists A(alias)] } { set A(alias) "Vo" }
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
set aliasSet 0
while { $w != $null } {
    set ait [$w NewAliasesIter $st]
    set a [$ait NextAlias $st]
    while { $a != $null } {
        set an "?"
        catch { set ca [DboTclHelper_sMakeCString]; $a GetName $ca; set an [DboTclHelper_sGetConstCharPtr $ca] }
        if { $an == "Vo" || $an == "Vo1" } {
            if { $an != $A(alias) } {
                catch { $a SetName [DboTclHelper_sMakeCString $A(alias)] }
                lappend out "alias: $an -> $A(alias)"
            } else {
                lappend out "alias: $an (保持)"
            }
            set aliasSet 1
        }
        set a [$ait NextAlias $st]
    }
    delete_DboWireAliasesIter $ait
    set w [$wit NextWire $st]
}
delete_DboPageWiresIter $wit
if { !$aliasSet } { lappend out "WARN: 未找到 Vo/Vo1 别名" }
join $out " | "
