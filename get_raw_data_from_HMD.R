# HMD Data Download and Processing Script
# Purpose: To obtain UK and USA mortality data (2015-2023) by age and gender
# Storage Paths:
# - Raw data: /data/raw/hmd/
# - Cleaned data: /data/processed/

# 1. Install and load necessary packages
if (!requireNamespace("hmd", quietly = TRUE)) {
  install.packages("hmd")
}
if (!requireNamespace("dplyr", quietly = TRUE)) {
  install.packages("dplyr")
}
if (!requireNamespace("readr", quietly = TRUE)) {
  install.packages("readr")
}
library(hmd)
library(dplyr)
library(readr)

# 2. Read HMD account information
# In GitHub Actions, this can be set via SECRETS; for local use, manual input is required
hmd_username <- Sys.getenv("HMD_USERNAME")
hmd_password <- Sys.getenv("HMD_PASSWORD")

# If environment variables are not set, prompt user for input (local testing only)
if (hmd_username == "" || hmd_password == "") {
  hmd_username <- readline("Enter HMD account email: ")
  hmd_password <- readline("Enter HMD password: ")
}

# 3. Define country codes and time range
country_codes <- c("gbr", "usa")  # UK (gbr), USA (usa)
year_range <- 2015:2023
age_range <- 0:120  # HMD standard age range

# 4. Data download function (by country and gender)
download_hmd_data <- function(country, year_range, age_range, username, password) {
  message(paste("Downloading data for", country))
  data_list <- list()
  
  # Loop through male/female data
  for (sex in c("m", "f")) {
    # Use getHMDweb function to retrieve data
    hmd_data <- getHMDweb(
      country = country,
      username = username,
      password = password,
      years = year_range,
      age = age_range,
      sex = sex,
      type = "standard"
    )
    
    # Data cleaning: extract necessary fields and standardize format
    cleaned_data <- hmd_data %>%
      dplyr::select(
        year = Year,
        age = Age,
        gender = Sex,  # m/f
        qx = qx.all
      ) %>%
      dplyr::mutate(
        gender = ifelse(gender == "m", "Male", "Female"),
        country = switch(country,
                         "gbr" = "UK",
                         "usa" = "USA"
        )
      )
    
    data_list[[sex]] <- cleaned_data
  }
  
  # Combine male and female data
  combined_data <- dplyr::bind_rows(data_list)
  return(combined_data)
}

# 5. Execute download and merge data
all_data <- NULL
for (country in country_codes) {
  country_data <- download_hmd_data(
    country = country,
    year_range = year_range,
    age_range = age_range,
    username = hmd_username,
    password = hmd_password
  )
  all_data <- dplyr::bind_rows(all_data, country_data)
}

# 6. Data validation and preview
message("Data download complete, validation in progress...")
print(paste("Total number of data rows:", nrow(all_data)))
print("First 10 rows of data:")
print(head(all_data, 10))

# 7. Data quality checks (example: missing value check)
missing_rate <- sum(is.na(all_data)) / (nrow(all_data) * ncol(all_data))
if (missing_rate > 0.01) {
  warning(paste("Warning: Missing value rate is", round(missing_rate * 100, 2), "%, exceeding the 1% threshold"))
} else {
  message(paste("Missing value rate is", round(missing_rate * 100, 2), "%, within acceptable limits"))
}

# 8. Save data (following project path conventions)
# Save raw data
raw_data_path <- "data/raw/hmd/hmd_uk_us_2015-2023.csv"
dir.create("data/raw/hmd", recursive = TRUE, showWarnings = FALSE)
write_csv(all_data, raw_data_path)
message(paste("Raw data saved to", raw_data_path))

# Save cleaned data (example: retain valid 2015-2023 data)
cleaned_data <- all_data %>%
  dplyr::filter(
    year %in% year_range,
    age >= 0,
    qx >= 0 & qx <= 1  # Filter out unreasonable mortality values
  )

processed_path <- "data/processed/cleaned_hmd.csv"
dir.create("data/processed", recursive = TRUE, showWarnings = FALSE)
write_csv(cleaned_data, processed_path)
message(paste("Cleaned data saved to", processed_path))

# 9. Generate summary report (for GitHub project documentation)
summary_report <- paste(
  "### HMD Data Download Report\n",
  "#### Data Overview\n",
  "- Countries:", paste(unique(all_data$country), collapse = ", "), "\n",
  "- Time Range:", min(year_range), "-", max(year_range), "\n",
  "- Age Range:", min(age_range), "-", max(age_range), "\n",
  "- Genders: Male, Female\n",
  "- Total Records:", nrow(all_data), "\n\n",
  "#### Field Description\n",
  "| Field | Description |\n",
  "|-------|-------------|\n",
  "| year  | Year        |\n",
  "| age   | Age         |\n",
  "| gender| Gender      |\n",
  "| qx    | Age-specific mortality rate |\n",
  "| country | Country    |\n\n",
  "#### Data Quality\n",
  "- Missing Value Rate:", round(missing_rate * 100, 2), "%\n",
  "- Valid qx Range:", min(cleaned_data$qx, na.rm = TRUE), "-", 
  max(cleaned_data$qx, na.rm = TRUE)
)

report_path <- "reports/hmd_download_summary.md"
dir.create("reports", recursive = TRUE, showWarnings = FALSE)
writeLines(summary_report, report_path)
message(paste("Data report saved to", report_path))
