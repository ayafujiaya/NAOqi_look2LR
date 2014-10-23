#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Leap, sys, thread, time
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

#import nao module
from naoqi import ALProxy

#ip & port setting
PORT = 9559
robotIP = "nao.local"

class SampleListener(Leap.Listener):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']

    def on_init(self, controller):
        global PORT, robotIP

        print "Initialized"

        self.motionProxy = ALProxy("ALMotion", robotIP, PORT)
        self.motionProxy.setStiffnesses("Head", 1.0)
        self.animatedSpeechProxy = ALProxy("ALAnimatedSpeech", robotIP, PORT)
        self.postureProxy = ALProxy("ALRobotPosture",robotIP, PORT)
        
        #ats
        self.configuration = {"bodyLanguageMode":"contextual"}

        result = self.postureProxy.goToPosture("Sit", 1.0)

        if(result):
            self.success()
        else:
            self.failure()
        pass

    def on_connect(self, controller):
        print "Connected"

        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        print "Exited"

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        #print "Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
        #      frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures()))

        # Get hands
        for hand in frame.hands:

            handType = "Left hand" if hand.is_left else "Right hand"

            #print "  %s, id %d, position: %s" % (handType, hand.id, hand.palm_position)

            # Get the hand's normal vector and direction
            normal = hand.palm_normal
            direction = hand.direction
            arm = hand.arm

            #naoの首が反応する閾値を設定  
            horizontalLimit = [-30.0, 30.0]
            verticalLimit   = [25.0, 35.0]

            #手の垂直と水平の値を取得
            horizontal = hand.palm_position[0]
            vertical   = hand.palm_position[1]

            #現在の水平の値が、naoの首の反応する閾値を超えているか判定　＆　超えていなければ０を代入
            if horizontal > horizontalLimit[1] or horizontal < horizontalLimit[0]:
                naoHorizontal = round(scale(horizontal, (-300.0, 300.0), (1.0, -1.0)), 2)
            else:
                naoHorizontal = 0
            
            #現在の垂直の値が、naoの首の反応する閾値を超えているか判定　＆　超えていなければ０を代入
            if vertical > verticalLimit[1] or vertical < verticalLimit[0]:
                naoVertical  = round(scale(vertical, (0.0, 500.0), (-0.7, +0.7)), 2)
            else:
                naoVertical = 0

            #現在の垂直の値が、naoの首の反応する閾値を超えているか判定　＆　超えていなければ０を代入
            if vertical < verticalLimit[1] and vertical > verticalLimit[0] and horizontal < horizontalLimit[1] and horizontal > horizontalLimit[0]:
                naoVertical = 0
                naoHorizontal = 0

            #現在の手の位置を比較し、水平か垂直か決定する
            if abs(naoVertical) > abs(naoHorizontal):
                naoHorizontal = 0
            elif abs(naoHorizontal) > abs(naoVertical):
                naoVertical = 0
                pass

            print "横方向 : ", horizontal, ", 縦方向 : ", vertical
            print "首横　 : ", naoHorizontal, ", 首縦　 : ", naoVertical
    
            
            # Example showing how to set angles, using a fraction of max speed
            names  = ["HeadYaw", "HeadPitch"]
            angles  = [naoHorizontal, naoVertical]
            #angles  = [0.2, -0.2]
            fractionMaxSpeed  = 0.7 
            self.motionProxy.setAngles(names, angles, fractionMaxSpeed)

            time.sleep(0.01)
            #self.motionProxy.setStiffnesses("Head", 0.0)

            

            # Get fingers
            for finger in hand.fingers:
                for b in range(0, 4):
                    bone = finger.bone(b)

        # Get tools
        for tool in frame.tools:
            pass

        # Get gestures
        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                circle = CircleGesture(gesture)

                # Determine clock direction using the angle between the pointable and the circle normal
                if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                    clockwiseness = "clockwise"
                else:
                    clockwiseness = "counterclockwise"

                # Calculate the angle swept since the last frame
                swept_angle = 0
                if circle.state != Leap.Gesture.STATE_START:
                    previous_update = CircleGesture(controller.frame(1).gesture(circle.id))
                    swept_angle =  (circle.progress - previous_update.progress) * 2 * Leap.PI

            if gesture.type == Leap.Gesture.TYPE_SWIPE:
                swipe = SwipeGesture(gesture)

            if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                keytap = KeyTapGesture(gesture)

            if gesture.type == Leap.Gesture.TYPE_SCREEN_TAP:
                screentap = ScreenTapGesture(gesture)
        #    print ""

    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"

def scale(val, src, dst):

    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]

def main():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        # Remove the sample listener when done
        controller.remove_listener(listener)


if __name__ == "__main__":
    main()
