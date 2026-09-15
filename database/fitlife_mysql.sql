CREATE TABLE auth_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    is_staff TINYINT(1) NOT NULL,
    is_superuser TINYINT(1) NOT NULL,
    is_active TINYINT(1) NOT NULL,
    last_login DATETIME NULL,
    date_joined DATETIME NOT NULL
);
 
CREATE TABLE auth_group (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);
 
CREATE TABLE auth_user_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    CONSTRAINT fk_aug_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_aug_group
        FOREIGN KEY (group_id) REFERENCES auth_group(id) ON DELETE CASCADE
);
 
CREATE TABLE user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    date_of_birth INT NOT NULL COMMENT 'Рік народження',
    weight FLOAT NOT NULL,
    height INT NOT NULL,
    fitness_goal VARCHAR(45) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    focus_muscle_group VARCHAR(20) NOT NULL,
    session_hours FLOAT NOT NULL,
    workouts_per_week SMALLINT NOT NULL,
    health_restrictions TEXT,
    CONSTRAINT fk_profile_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);
 
CREATE TABLE user_measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    weight FLOAT NOT NULL,
    height INT NOT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_measurements_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);
 
CREATE TABLE meal_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    daily_calorie INT NOT NULL,
    proteins INT NOT NULL,
    fats INT NOT NULL,
    carbs INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_meal_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);
 
CREATE TABLE workouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(45) NOT NULL,
    difficulty VARCHAR(45) NOT NULL COMMENT 'Easy / Medium / Hard',
    duration_min INT NOT NULL,
    url VARCHAR(250),
    program_text TEXT,
    is_ai_generated TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_workout_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);
 
CREATE TABLE user_workouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    workout_id INT NOT NULL,
    assigned_date DATE NOT NULL,
    CONSTRAINT uniq_user_workout UNIQUE (user_id, workout_id),
    CONSTRAINT fk_uw_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_uw_workout
        FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE
);
 
CREATE TABLE ai_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    request_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    kind VARCHAR(10) NOT NULL COMMENT 'plan / chat',
    recommendation_summary VARCHAR(1000) NOT NULL,
    CONSTRAINT fk_ai_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);
 
CREATE TABLE ai_log_workouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ai_log_id INT NOT NULL,
    workout_id INT NOT NULL,
    CONSTRAINT uniq_ailog_workout UNIQUE (ai_log_id, workout_id),
    CONSTRAINT fk_ailog_w_log
        FOREIGN KEY (ai_log_id) REFERENCES ai_logs(id) ON DELETE CASCADE,
    CONSTRAINT fk_ailog_w_workout
        FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE
);
 
CREATE TABLE ai_log_meal_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ai_log_id INT NOT NULL,
    meal_plan_id INT NOT NULL,
    CONSTRAINT uniq_ailog_mealplan UNIQUE (ai_log_id, meal_plan_id),
    CONSTRAINT fk_ailog_m_log
        FOREIGN KEY (ai_log_id) REFERENCES ai_logs(id) ON DELETE CASCADE,
    CONSTRAINT fk_ailog_m_meal
        FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE
);