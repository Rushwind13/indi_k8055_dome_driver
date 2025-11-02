Feature: Dome Rotation Operations
  As an observatory operator
  I want to rotate the dome in both directions
  So that I can position the dome correctly for observations

  Background:
    Given the dome controller is initialized
    And the dome is in a known state

  Scenario: Rotate dome clockwise by specific amount
    Given the dome is at a known position
    When I rotate the dome clockwise by 90 degrees
    Then the dome should rotate in the clockwise direction
    And the dome position should increase by 90 degrees
    And the rotation should complete successfully

  Scenario: Rotate dome counter-clockwise by specific amount
    Given the dome is at a known position
    When I rotate the dome counter-clockwise by 45 degrees
    Then the dome should rotate in the counter-clockwise direction
    And the dome position should decrease by 45 degrees
    And the rotation should complete successfully

  Scenario: Rotate dome to specific azimuth
    Given the dome is at azimuth 0 degrees
    When I command the dome to move to azimuth 180 degrees
    Then the dome should rotate to azimuth 180 degrees
    And the final position should be 180 degrees
    And the rotation should use the shortest path

  Scenario: Rotate dome beyond 360 degrees
    Given the dome is at azimuth 350 degrees
    When I rotate the dome clockwise by 30 degrees
    Then the dome should handle the wraparound correctly
    And the final position should be 20 degrees (380 - 360)

  Scenario: Stop dome rotation mid-movement
    Given the dome is rotating clockwise
    When I send a stop command
    Then the dome should stop rotating immediately
    And the current position should be recorded
    And no further movement should occur

  Scenario: Attempt rotation with insufficient power
    Given the dome hardware has insufficient power
    When I attempt to rotate the dome
    Then the rotation command should fail
    And an appropriate error should be reported
    And the dome position should remain unchanged

  Scenario: Rotation timeout handling
    Given the dome rotation is taking longer than expected
    When the rotation timeout is reached
    Then the rotation should be stopped
    And a timeout error should be reported
    And the dome should be in a safe state
