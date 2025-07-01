LIBNAME cdc_data '/path/to/cdc_data';

PROC IMPORT DATAFILE="cdc_usa_excess_mortality.csv" 
            OUT=WORK.CDC_USA_RAW 
            DBMS=CSV 
            REPLACE;
RUN;

PROC IMPORT DATAFILE="cdc_uk_excess_mortality.csv" 
            OUT=WORK.CDC_UK_RAW 
            DBMS=CSV 
            REPLACE;
RUN;

PROC CONTENTS DATA=WORK.CDC_USA_RAW;
RUN;

PROC CONTENTS DATA=WORK.CDC_UK_RAW;
RUN;

DATA WORK.CDC_USA_CLEANED;
    SET WORK.CDC_USA_RAW;
    IF NOT missing(date) THEN formatted_date = INPUT(date, ANYDTDTE.);
    FORMAT formatted_date DATE9.;
    ARRAY num_vars(*) excess_deaths expected_deaths;
    DO i = 1 TO DIM(num_vars);
        IF missing(num_vars[i]) THEN num_vars[i] = .;
    END;
    IF excess_deaths < 0 THEN excess_deaths = 0;
RUN;

DATA WORK.CDC_UK_CLEANED;
    SET WORK.CDC_UK_RAW;
    IF NOT missing(date) THEN formatted_date = INPUT(date, ANYDTDTE.);
    FORMAT formatted_date DATE9.;
    ARRAY num_vars(*) excess_deaths expected_deaths;
    DO i = 1 TO DIM(num_vars);
        IF missing(num_vars[i]) THEN num_vars[i] = .;
    END;
    IF excess_deaths < 0 THEN excess_deaths = 0;
RUN;

PROC REPORT DATA=WORK.CDC_USA_CLEANED NOWINDOWS HEADLINE;
    COLUMN variable n mean std min max nmiss pctmiss;
    DEFINE variable / GROUP FORMAT=$32. 'Variable';
    DEFINE n / DISPLAY FORMAT=8. 'Observations';
    DEFINE mean / DISPLAY FORMAT=8.2 'Mean';
    DEFINE std / DISPLAY FORMAT=8.2 'Std Dev';
    DEFINE min / DISPLAY FORMAT=8.2 'Min';
    DEFINE max / DISPLAY FORMAT=8.2 'Max';
    DEFINE nmiss / DISPLAY FORMAT=8. 'Missing Values';
    DEFINE pctmiss / DISPLAY FORMAT=6.2 'Missing Rate(%)';
    TITLE 'CDC US Excess Mortality Data Cleaning Report';
RUN;

PROC REPORT DATA=WORK.CDC_UK_CLEANED NOWINDOWS HEADLINE;
    COLUMN variable n mean std min max nmiss pctmiss;
    DEFINE variable / GROUP FORMAT=$32. 'Variable';
    DEFINE n / DISPLAY FORMAT=8. 'Observations';
    DEFINE mean / DISPLAY FORMAT=8.2 'Mean';
    DEFINE std / DISPLAY FORMAT=8.2 'Std Dev';
    DEFINE min / DISPLAY FORMAT=8.2 'Min';
    DEFINE max / DISPLAY FORMAT=8.2 'Max';
    DEFINE nmiss / DISPLAY FORMAT=8. 'Missing Values';
    DEFINE pctmiss / DISPLAY FORMAT=6.2 'Missing Rate(%)';
    TITLE 'CDC UK Excess Mortality Data Cleaning Report';
RUN;

PROC EXPORT DATA=WORK.CDC_USA_CLEANED 
              OUTFILE="cdc_usa_cleaned.csv" 
              DBMS=CSV 
              REPLACE;
RUN;

PROC EXPORT DATA=WORK.CDC_UK_CLEANED 
              OUTFILE="cdc_uk_cleaned.csv" 
              DBMS=CSV 
              REPLACE;
RUN;
