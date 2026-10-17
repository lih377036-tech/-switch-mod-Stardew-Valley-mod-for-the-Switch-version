#pragma once
#include <cstdint>
namespace AutomateLite::UIInfo::MenuInput {
inline constexpr int Up=1;
inline constexpr int Down=2,Left=4,Right=8,Confirm=0x1000,Cancel=0x2000;
// MonoGame Buttons enum; stick-direction events are not D-pad events.
// LeftThumbstickLeft is 0x200000, not 0x40000000 (which is Right).
inline constexpr int StickLeft=0x200000,StickRight=0x40000000;
inline constexpr int StickUp=0x10000000,StickDown=0x20000000;
constexpr int Direction(int button) {
    if(button==StickLeft)return Left;
    if(button==StickRight)return Right;
    if(button==StickUp)return Up;
    if(button==StickDown)return Down;
    return button;
}
inline constexpr int LeftTrigger=0x800000,RightTrigger=0x400000;
enum class Action { Pass,Open,Consume,Settings };
constexpr Action Route(int button,bool left,bool right,bool open,bool canEnter,bool latched) {
    if(!open && button==Up && left && right)
        return canEnter && !latched ? Action::Open : Action::Consume;
    return open ? Action::Settings : Action::Pass;
}
struct Latch {
    bool down{};
    constexpr void Observe(bool connected,bool upHeld) { if(!connected || !upHeld) down=false; }
};
enum class HammerAction { Pass,Focus,BlurPass,BlurConsume,Open,Consume };
constexpr HammerAction RouteHammer(int button,bool focused,bool hovered,bool beside,bool canEnter) {
    button=Direction(button);
    if(button==Confirm && (focused || hovered))
        return canEnter ? HammerAction::Open : HammerAction::Consume;
    if(focused) {
        if(button==Left || button==Cancel) return HammerAction::BlurConsume;
        if(button==Right || button==Up) return HammerAction::Consume;
        return HammerAction::BlurPass;
    }
    if(button==Right && beside) return HammerAction::Focus;
    return HammerAction::Pass;
}
struct EntryGate {
    std::uint64_t last{};
    bool activated{};
    constexpr bool Recent(std::uint64_t now) const { return activated && now-last<250; }
    constexpr bool Accept(std::uint64_t now) {
        if(Recent(now)) return false;
        last=now;activated=true;return true;
    }
};
}
