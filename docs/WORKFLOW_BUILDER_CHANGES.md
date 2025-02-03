# Workflow Builder Changes

## Overview

The Workflow Builder has been redesigned to support a more flexible, module-based configuration system. This document outlines the key changes and improvements made to the workflow building process.

## Key Changes

### 1. Module-Based Configuration

#### Old Format:
- Fixed task sequence
- Hardcoded dependencies
- Limited configuration options

#### New Format:
```json
{
    "modules": {
        "module_id": {
            "identifier": "component_type",
            "user_config": {
                "param": "value",
                "dependent_param": {
                    "module_id": "other_module",
                    "output_key": "output_field"
                }
            }
        }
    }
}
```

Benefits:
- Dynamic task ordering
- Flexible dependency management
- Enhanced configuration capabilities
- Self-documenting module relationships

### 2. Dependency Resolution

#### Improvements:
- Automatic dependency detection from module configurations
- Topological sorting for optimal task ordering
- Circular dependency detection and prevention
- Clear error reporting for dependency issues

#### Example:
```python
dependencies = {
    "document_processor": {"s3_downloader"},
    "embeddings_generator": {"document_preprocessor"},
    "vector_store": {"embeddings_generator"}
}
```

### 3. Parameter Resolution

#### New Features:
- Dynamic parameter resolution from dependencies
- Conductor-style parameter references (${task.output.field})
- Support for both direct values and module references
- Validation of parameter dependencies

### 4. Validation System

New validation checks:
- Module existence verification
- Required field validation
- Dependency reference validation
- Configuration structure validation
- Circular dependency detection

### 5. Error Handling

Improved error handling with:
- Detailed error messages
- Validation failure reporting
- Dependency resolution errors
- Configuration parsing errors
- Task creation failures

## Migration Guide

### Updating Existing Configurations

1. Convert task definitions to modules:
```json
// Old
{
    "tasks": [
        {
            "name": "download",
            "config": {}
        }
    ]
}

// New
{
    "modules": {
        "download_001": {
            "identifier": "s3_downloader",
            "user_config": {}
        }
    }
}
```

2. Update dependencies to use module references:
```json
// Old
"input": "previous_task.output"

// New
"input": {
    "module_id": "previous_module",
    "output_key": "output_field"
}
```

### Code Updates

1. Use new builder initialization:
```python
# Old
builder = WorkflowBuilder(tasks)

# New
builder = WorkflowBuilder(config)
```

2. Update task references:
```python
# Old
task_output = task.get_output()

# New
module_output = task_input.get('user_config').get('input_field')
```

## Best Practices

1. **Module Naming**
   - Use descriptive module IDs
   - Follow consistent naming conventions
   - Include component type in ID

2. **Configuration Structure**
   - Group related modules
   - Keep configurations focused
   - Document dependencies clearly

3. **Dependency Management**
   - Minimize dependency chains
   - Avoid circular dependencies
   - Document data flow

4. **Error Handling**
   - Validate configurations early
   - Provide clear error messages
   - Handle edge cases gracefully

## Testing

New test cases added:
- Configuration validation
- Dependency resolution
- Parameter mapping
- Error handling
- Edge cases

Example test:
```python
def test_workflow_builder():
    config = {
        "modules": {
            "download_001": {
                "identifier": "s3_downloader",
                "user_config": {}
            }
        }
    }
    builder = WorkflowBuilder(config)
    assert builder.validate_config()