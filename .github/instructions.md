## DIGiDIG — Copilot / AI Agent Instructions

## ⚠️ CRITICAL RULES - READ FIRST EVERY TIME ⚠️

### 🚨 ABSOLUTE REQUIREMENTS - NEVER VIOLATE THESE:

1. **ALWAYS USE .venv - NEVER SYSTEM PYTHON**
   - ❌ FORBIDDEN: Running any Python command without `.venv` active
   - ❌ FORBIDDEN: Using `python3` or `pip` directly
   - ✅ REQUIRED: Use `.venv/bin/python` and `.venv/bin/pip` explicitly
   - ✅ REQUIRED: Check terminal has `(.venv)` in prompt before running commands
   - ✅ REQUIRED: If terminal lacks .venv, activate it first: `source .venv/bin/activate`

2. **NEVER RUN COMMANDS DIRECTLY ON USER'S MACHINE**
   - ❌ FORBIDDEN: `sudo apt-get install`, `certbot`, manual Docker commands
   - ❌ FORBIDDEN: Any system-level changes outside Makefile
   - ✅ REQUIRED: ALL operations must be in Makefile targets
   - ✅ REQUIRED: Use `make <target>` for all operations
   - ✅ REQUIRED: If functionality doesn't exist in Makefile, ADD IT TO MAKEFILE FIRST

3. **ALWAYS VERIFY YOUR CHANGES IMMEDIATELY**
   - ❌ FORBIDDEN: Making changes without testing them
   - ❌ FORBIDDEN: Assuming something works without verification
   - ✅ REQUIRED: After ANY change, run `make install` or appropriate make target
   - ✅ REQUIRED: Check logs/output to confirm changes work
   - ✅ REQUIRED: Test the feature you just implemented

4. **LET'S ENCRYPT IS PRIORITY - NOT SELF-SIGNED**
   - ❌ FORBIDDEN: Defaulting to self-signed certificates
   - ❌ FORBIDDEN: Ignoring user's repeated requests for Let's Encrypt
   - ✅ REQUIRED: Always attempt Let's Encrypt FIRST in `make install`
   - ✅ REQUIRED: Self-signed is ONLY fallback when Let's Encrypt fails
   - ✅ REQUIRED: Clearly report WHY Let's Encrypt failed if it does

5. **ALWAYS USE CORRECT HOSTNAMES FROM CONFIG**
   - ❌ FORBIDDEN: Hardcoding `localhost` or IP addresses
   - ❌ FORBIDDEN: Ignoring hostname in config.yaml or .env
   - ✅ REQUIRED: Read hostname from config.yaml `external_url` or .env `HOSTNAME`
   - ✅ REQUIRED: Use config values in URLs, not assumptions

6. **COMMUNICATE CLEARLY AND VERIFY UNDERSTANDING**
   - ❌ FORBIDDEN: Making assumptions about what user wants
   - ❌ FORBIDDEN: Repeating same mistakes after correction
   - ✅ REQUIRED: If uncertain, ask clarifying questions
   - ✅ REQUIRED: Acknowledge when you've made an error
   - ✅ REQUIRED: Learn from corrections and don't repeat them

### 📋 WORKFLOW CHECKLIST - FOLLOW FOR EVERY TASK:

1. ✅ Check terminal has `.venv` active (look for `(.venv)` in prompt)
2. ✅ Read config.yaml/.env for current settings (hostname, ports, etc.)
3. ✅ Plan changes in Makefile, NOT as direct commands
4. ✅ Make changes to code/config
5. ✅ Test changes with `make install` or appropriate target
6. ✅ Verify logs/output show success
7. ✅ Report results to user with evidence (logs, output)

---

## Project Structure and Standards

1. **Understanding the Project Structure**:
   - The DIGiDIG project is organized into multiple microservices located in the `services/` directory.
   - Shared components and utilities are housed in the `lib/` directory.
   - Configuration files are stored in the `config/` directory.
   - Documentation is found in the `_doc/` directory. 
2. **Coding Standards**:
   - Follow PEP 8 guidelines for Python code.
   - Use consistent naming conventions (e.g., `snake_case` for variables and functions, `CamelCase` for classes).
   - Write clear and concise docstrings for all public modules, classes, and functions.  
   - Use modules, OOP, SOLID, DRY, and KISS principles where applicable.
3. **Testing**:
   - Write unit tests for all new features and bug fixes. 
    - Place tests in the `_test/` directory, following the existing structure for unit and integration tests.
    - Ensure tests cover edge cases and validate expected behavior.
4. **Version Control**:
   - Use Git for version control.
   - Write meaningful commit messages that describe the changes made.
   - Create feature branches for new features and bug fixes, and merge them into the main branch via pull requests after review.
    - Regularly pull updates from the main branch to keep your feature branch up to date.
5. **Documentation**:
   - Update the documentation in the `_doc/` directory to reflect any changes made to the project.
   - Include usage examples, configuration instructions, and any relevant diagrams or flowcharts.
6. **Code Reviews**:
   - Conduct code reviews for all pull requests.
   - Provide constructive feedback and suggestions for improvement.
   - Ensure that code changes align with project standards and best practices.
7. **Security and Privacy**:
   - Follow best practices for handling sensitive data.
   - Ensure that configuration files do not contain hardcoded secrets or credentials.
   - Use environment variables or secure vaults for sensitive information.
8. **Continuous Integration/Continuous Deployment (CI/CD)**:
    - Integrate with CI/CD pipelines to automate testing and deployment.
    - Ensure that all tests pass before merging code into the main branch.
    - Use `docker compose` for building and orchestrating services (not `docker-compose`).
    - Follow deployment procedures outlined in the project documentation.
9. **Performance Optimization**:
    - Monitor and optimize the performance of services.
    - Profile code to identify bottlenecks and improve efficiency.
    - Use caching strategies where appropriate to enhance performance.
10. **Collaboration and Communication**:
    - Communicate effectively with team members regarding project progress and challenges.
    - Atlassian tools (Jira, Confluence) are used for task management and documentation.
    - Participate in regular team meetings and code walkthroughs.
11. **Services and Apps**:
    - Each service in the `services/` directory should have a clear purpose and responsibility.
    - Ensure that services communicate effectively with each other using defined APIs or messaging protocols.
    - Maintain service isolation to prevent unintended dependencies.
    - Service will be either server side with REST API (FastAPI) or client side with web UI (HTML/CSS/JS).
    - Apps should be designed with user experience in mind, ensuring accessibility and responsiveness.
    - Apps should follow modern web development practices and standards.
    - Apps should use UI frameworks/libraries written as a shared component in the `lib/` directory where applicable.
12. **Shared Libraries**:
    - Use the `lib/` directory for shared code and utilities.
    - Ensure that shared libraries are well-documented and tested.
    - Avoid circular dependencies between services and shared libraries.  
    - MVC architecture should be followed where applicable.
    - Include comprehensive tests for all shared libraries.
13. **Configuration Management**:
    - Use the `config/` directory for managing configuration files.
    - Ensure that configuration files are environment-specific (e.g., development, staging, production).
    - Document configuration options and their usage in the `_doc/CONFIGURATION.md` file.