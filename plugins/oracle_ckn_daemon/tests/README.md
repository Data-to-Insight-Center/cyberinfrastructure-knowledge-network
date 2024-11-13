CKN Oracle Daemon plugin tests:

1. Install requirements:
```bash
  pip install -r requirements.txt
  ```

2. **Start up CKN and Produce Oracle Events**
   Refer to the [Getting Started](../README.md) section.

3. **Run Tests**:
   - Test if events are stored in Knowledge Graph:
   ```bash
    pytest test_ckn_oracle_daemon.py
   ```
   
   - Test when POWER_MONITORING is enabled:
   ```bash
    pytest test_power_monitoring_false.py
   ```
   
   - Test when POWER_MONITORING is disabled:
   ```bash
    pytest test_power_monitoring_true.py
   ```
   
   - Test CKN Stream Processors:
   ```bash
    pytest test_ckn_stream_processor.py
   ```