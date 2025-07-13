library(HMDHFDplus)
library(readr)
library(dplyr)

# 安全凭证获取函数
get_hmd_credentials <- function() {
  # 尝试从GitHub Actions环境变量获取
  username <- Sys.getenv("HMD_USERNAME")
  password <- Sys.getenv("HMD_PASSWORD")
  
  if (!is.null(username) && nchar(username) > 0 &&
      !is.null(password) && nchar(password) > 0) {
    return(list(username = username, password = password))
  }
  
  # 本地开发环境备用方案
  tryCatch({
    cred_file <- file.path(Sys.getenv("HOME"), ".hmd_credentials")
    if (file.exists(cred_file)) {
      cred <- readLines(cred_file)
      return(list(
        username = trimws(cred[1]),
        password = trimws(cred[2])
      ))
    }
  }, error = function(e) NULL)
  
  stop("无法获取HMD凭证")
}

# 主获取函数
fetch_hmd_data <- function() {
  cred <- get_hmd_credentials()
  
  # 获取美国死亡率数据 (2015-2023)
  data <- tryCatch({
    readHMDweb(
      CNTRY = "USA",
      item = "Mx_1x1",
      username = cred$username,
      password = cred$password
    )
  }, error = function(e) {
    message("HMD数据获取失败: ", e$message)
    stop(e)
  })
  
  # 筛选核心数据
  filtered_data <- data %>%
    filter(Year >= 2015, Year <= 2023,
           Age %in% c(20, 25, 30, 60, 80, 84)) %>%
    select(Year, Age, Female, Male, Total)
  
  # 创建数据目录（使用绝对路径避免相对路径问题）
  data_dir <- file.path(getwd(), "data")
  if (!dir.exists(data_dir)) {
    dir.create(data_dir, recursive = TRUE)
    message("创建数据目录: ", data_dir)
  }
  
  # 保存为CSV
  write_csv(filtered_data, file.path(data_dir, "hmd_usa_2015-2023.csv"))
  message("数据已保存至: ", file.path(data_dir, "hmd_usa_2015-2023.csv"))
  
  # 生成数据摘要
  summary_data <- filtered_data %>%
    group_by(Age) %>%
    summarise(
      Avg_Mortality = mean(Total, na.rm = TRUE),
      Min_Year = min(Year),
      Max_Year = max(Year)
    )
  
  write_csv(summary_data, file.path(data_dir, "hmd_summary.csv"))
  message("摘要已保存至: ", file.path(data_dir, "hmd_summary.csv"))
}

# 执行数据获取
fetch_hmd_data()
message("HMD数据获取成功")
