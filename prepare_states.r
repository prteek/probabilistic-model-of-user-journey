# %%
library(tidyverse)

setwd(this.path::here())

# %%
dau_data <- read_csv("dau_data.csv", show_col_types = FALSE)

start_date <- min(dau_data$date)
end_date <- max(dau_data$date)

# %%
full_dates <- tibble(expand.grid(
    date = seq(start_date, end_date, by = "day"),
    user_id = unique(dau_data$user_id)
))

all_active_days <- left_join(
    full_dates,
    dau_data %>%
        mutate(is_active = TRUE, last_active_date = date),
    by = c("date", "user_id")
)

# %%
# The code below fills NA in registration date by user id to enable filter subsequently
filtered_active_days <- all_active_days %>%
    group_by(user_id) %>%
    mutate(
        registration_date = coalesce(
            registration_date,
            first(na.omit(registration_date))
        ),
        is_active = coalesce(is_active, FALSE),
        first_active_date = first(na.omit(last_active_date))
    ) %>%
    ungroup() %>%
    filter(date >= pmax(registration_date, first_active_date))

head(filtered_active_days)

# %%
# Code below fills last active date to be used for state assignment
states <- filtered_active_days %>%
    group_by(user_id) %>%
    arrange(date) %>%
    fill(last_active_date, .direction = "down") %>%
    mutate(last_active_date = coalesce(lag(last_active_date), date)) %>%
    ungroup() %>%
    mutate(
        state = case_when(
            date == registration_date ~ "new",
            (date != registration_date) &
                (is_active == TRUE) &
                (as.numeric(date - last_active_date) <= 6) ~ "current",
            (is_active == TRUE) &
                (as.numeric(date - last_active_date) <= 30) &
                (as.numeric(date - last_active_date) > 6) ~ "reactivated",
            (is_active == TRUE) &
                (as.numeric(date - last_active_date) > 30) ~ "resurrected",
            (is_active == FALSE) &
                (as.numeric(date - last_active_date) <= 6) ~ "at_risk_wau",
            (is_active == FALSE) &
                (as.numeric(date - last_active_date) <= 30) &
                (as.numeric(date - last_active_date) > 6) ~ "at_risk_mau",
            TRUE ~ "dormant"
        )
    ) %>%
    dplyr::select(user_id, date, is_active, state, registration_date)

write.csv(states, "states.csv", row.names = FALSE)

# %%
