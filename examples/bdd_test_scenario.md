# Block Definition Diagram Test Scenario: CoffeeMachine

## Test Scenario Overview
**Zweck**: Demonstration der BDD-Erstellung mit verschiedenen SysML Block-Typen und Layouts

## Test Elements

### Primary Blocks (SysML1.4::Block)
1. **CoffeeMachine** (Main System Block)
   - Attributes: powerState, waterLevel, coffeeBeansLevel
   - Operations: powerOn(), powerOff(), brewCoffee()

2. **Boiler** (Heating Subsystem)
   - Attributes: temperature, capacity, isHeating
   - Operations: heatWater(), getTemperature(), maintainTemperature()

3. **Pump** (Pressure System)
   - Attributes: flowRate, pressure, isRunning
   - Operations: start(), stop(), setPressure()

4. **Grinder** (Processing Unit)
   - Attributes: grindLevel, isGrinding
   - Operations: grindBeans(), setGrindLevel()

5. **WaterTank** (Storage Component)
   - Attributes: capacity, currentLevel
   - Operations: fill(), checkLevel()

### Control Elements (Class/Component)
6. **ControlUnit** (Controller)
   - Type: Class with "controller" stereotype
   - Attributes: currentState, selectedProgram
   - Operations: executeProgram(), checkSensors()

## BDD Layout Tests

### Test Case 1: Compact Layout (3x2 Grid)
- **Elements**: CoffeeMachine, Boiler, Pump, Grinder, WaterTank, ControlUnit
- **Grid**: 3 columns, 2 rows
- **Cell Size**: 280x200px
- **Purpose**: Test standard compact layout

### Test Case 2: Wide Layout (4x2 Grid) 
- **Elements**: All 6 elements
- **Grid**: 4 columns, 2 rows  
- **Cell Size**: 320x220px
- **Purpose**: Test wider layout with more space

### Test Case 3: Vertical Layout (2x3 Grid)
- **Elements**: Core blocks only (CoffeeMachine, Boiler, Pump, Grinder)
- **Grid**: 2 columns, 3 rows
- **Cell Size**: 350x250px
- **Purpose**: Test vertical arrangement

### Test Case 4: Single Row (6x1 Grid)
- **Elements**: All elements in horizontal line
- **Grid**: 6 columns, 1 row
- **Cell Size**: 250x300px
- **Purpose**: Test horizontal layout

## Expected Results

1. **Diagram Creation**: BDD successfully created in target package
2. **Element Placement**: All elements positioned in correct grid positions
3. **Coordinate System**: EA's inverted Y-axis handled correctly
4. **Element Display**: Blocks show attributes and operations
5. **MDG Support**: SysML blocks created with proper stereotypes
6. **Fallback Handling**: Class fallback when SysML not available

## Success Criteria

- ✅ Diagram created without errors
- ✅ All elements visible on diagram
- ✅ Grid layout properly arranged
- ✅ No overlapping elements
- ✅ Element details (attributes/operations) visible
- ✅ Proper SysML Block stereotypes applied