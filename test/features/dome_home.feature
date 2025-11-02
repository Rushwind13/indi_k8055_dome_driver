Feature: Dome Home Position Operations
  As an observatory operator
  I want to move the dome to its home position
  So that I can safely operate the shutter and perform maintenance

  Background:
    Given the dome controller is initialized
    And the dome position is being tracked

  Scenario: Move dome to home position from arbitrary location
    Given the dome is at azimuth 180 degrees
    And the dome is not at home position
    When I command the dome to move to home position
    Then the dome should rotate toward the home position
    And the home switch should be detected
    And the dome should stop at the home position
    And the dome position should be reset to home value
    And the dome status should show "at home"

  Scenario: Dome already at home position
    Given the dome is already at home position
    When I command the dome to move to home position
    Then no movement should occur
    And the dome should remain at home position
    And a message should indicate already at home

  Scenario: Home position detection failure
    Given the dome is moving toward home position
    And the home switch is not functioning
    When the dome reaches the expected home position
    Then a timeout should occur
    And an error should be reported
    And the dome should stop in a safe state
    And manual intervention should be required

  Scenario: Home switch bouncing detection
    Given the dome is approaching home position
    When the home switch triggers intermittently
    Then the dome should use debounce logic
    And false triggers should be ignored
    And the dome should stop only on stable home detection

  Scenario: Power loss during homing
    Given the dome is moving to home position
    When power is lost to the dome motor
    Then the dome should stop immediately
    And the position should be marked as unknown
    And a power failure error should be reported
    And recovery procedures should be available
