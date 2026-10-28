set out {}
foreach it { Bias Bias.sim Tran Tran.sim } {
    set r [catch { SelectPMItem $it } rv]
    lappend out "sel $it -> rc=$r val=$rv"
}
return $out
