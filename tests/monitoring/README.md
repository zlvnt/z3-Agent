# Monitoring Tests

Test suite untuk Phase 1 monitoring implementation.

## Test Files

### `test_monitoring_phase1.py` ⭐
**Main comprehensive test** untuk semua Phase 1 features:
- File logging callbacks
- Basic metrics collection  
- Health endpoints functionality
- Chain integration dengan monitoring
- Log file content verification

```bash
python tests/monitoring/test_monitoring_phase1.py
```

### `test_log_rotation.py`
**Log rotation functionality testing:**
- Size-based rotation
- Gzip compression
- Auto-rotation demonstration
- Old file cleanup
- Rotation status monitoring

```bash
python tests/monitoring/test_log_rotation.py
```

### `test_endpoints.py`
**HTTP endpoints testing:**
- FastAPI server startup testing
- Health check endpoints (`/health`, `/ready`, `/metrics/basic`)
- Direct function testing mode
- HTTP vs direct function comparison

```bash
# Full HTTP testing (starts server)
python tests/monitoring/test_endpoints.py

# Direct testing (faster, no server)
python tests/monitoring/test_endpoints.py --direct
```

### `example_monitoring.py`
**Development example** untuk callback system:
- Mock chain execution
- Performance callback examples  
- Different callback implementations
- Chain monitoring demonstration

```bash
python tests/monitoring/example_monitoring.py
```

## Usage

### Run All Tests
```bash
# From project root
python tests/monitoring/test_monitoring_phase1.py
python tests/monitoring/test_log_rotation.py
python tests/monitoring/test_endpoints.py --direct
```

### Quick Health Check
```bash
# Test if monitoring system is working
python tests/monitoring/test_endpoints.py --direct
```

### Development Testing
```bash
# Test callback system during development
python tests/monitoring/example_monitoring.py
```

## Test Coverage

✅ **File Logging**: JSON Lines format, severity classification  
✅ **Metrics Collection**: Request/error tracking, performance stats  
✅ **Health Endpoints**: System health, readiness checks  
✅ **Log Rotation**: Size-based rotation, compression  
✅ **Chain Integration**: Callback system, monitoring flow  
✅ **Error Handling**: Graceful callback failures  

## Test Data

Tests create temporary files in:
- `logs/monitoring.jsonl` - Main log file
- `logs/monitoring_*.jsonl.gz` - Rotated log files

Test data is automatically cleaned up after rotation tests.

---

*Phase 1 monitoring implementation tests - All functionality verified* ✅