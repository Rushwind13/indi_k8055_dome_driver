Feature: Telemetry and Status Monitoring
  As an observatory operator
  I want to monitor dome telemetry and status
  So that I can ensure safe and proper dome operation

  Background:
    Given the dome controller is initialized
    And telemetry systems are functioning

  Scenario: Read dome position telemetry
    Given the dome is at a known position
    When I request the current dome position
    Then the position should be returned in degrees
    And the position should be accurate to within 1 degree
    And the timestamp should be current

  Scenario: Monitor encoder tick counts
    Given the dome encoders are functioning
    When I read the encoder values
    Then encoder A and B values should be returned
    And the values should correspond to the current position
    And the encoder values should be consistent

  Scenario: Check dome movement status
    Given the dome is rotating clockwise
    When I check the movement status
    Then the status should show "turning"
    And the direction should show "clockwise"
    And the target position should be available

  Scenario: Monitor home switch status
    Given the dome is at various positions
    When I check the home switch status
    Then the switch should read true only at home position
    And the switch should read false at all other positions
    And the switch status should be reliable

  Scenario: Check shutter position status
    Given the shutter is in various positions
    When I check the shutter status
    Then the status should accurately reflect open/closed/intermediate
    And the status should be consistent with limit switches
    And the last operation timestamp should be available

  Scenario: Monitor system health
    Given all dome systems are operational
    When I request a system health check
    Then all subsystems should report healthy status
    And any errors or warnings should be flagged
    And diagnostic information should be available

  Scenario: Detect communication failures
    Given the dome controller is running
    When communication with hardware is lost
    Then a communication error should be detected
    And the error should be logged with timestamp
    And safe mode should be activated

  Scenario: Handle sensor failures
    Given position sensors are being monitored
    When a sensor fails or gives inconsistent readings
    Then the failure should be detected
    And an alert should be generated
    And fallback procedures should be activated

  Scenario: Monitor power levels
    Given the dome systems are powered
    When I check power status
    Then voltage levels should be within acceptable ranges
    And any power anomalies should be detected
    And power history should be available
