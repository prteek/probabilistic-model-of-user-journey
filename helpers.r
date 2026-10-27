# %%
suppressPackageStartupMessages(library(tidyverse))

# %%

get_transition_matrix <- function(states_slice) {
    suppressMessages(
        M <- states_slice %>%
            group_by(user_id) %>%
            arrange(date) %>%
            mutate(
                state_to = lead(state),
                state_from = state
            ) %>%
            ungroup() %>%
            # Remove the last row since user doesn't transition to anywhere from that
            filter(!is.na(state_to)) %>%
            # Count transitions per user to avoid counting transitions across users
            group_by(user_id, state_from, state_to) %>%
            summarise(transition_count = n()) %>%
            ungroup() %>%
            # Sum all the transitions over all users
            group_by(state_from, state_to) %>%
            summarise(transition_count = sum(transition_count)) %>%
            ungroup() %>%
            # Generates a wide form matrix from long form
            pivot_wider(names_from = state_to, values_from = transition_count, values_fill = list(transition_count = 0)) %>%
            # Normalizes matrix of counts so that rows sum to 1
            mutate(row_sum = rowSums(dplyr::select(., -state_from))) %>%
            mutate(across(-state_from, ~ . / row_sum)) %>%
            dplyr::select(-row_sum) %>%
            # Generates ordered matrix where row and column name orders match
            mutate(new = 0) %>% # To get consistent matrix since 'new' is missing from state_to
            column_to_rownames("state_from") %>%
            .[order(rownames(.)), order(colnames(.))]
    )
    return(M)
}

# %%

predict_dau <- function(M, state0, start_date, end_date, new_users_predicted) {
    dates <- seq(as.Date(start_date), as.Date(end_date), by = "day")
    new_dau <- state0[match(state0$state, rownames(M)), ]$cnt # Align state0 to transition Matrix name order
    dau_pred <- list()

    for (dt in dates) {
        new_dau <- as.integer(t(M) %*% new_dau)
        new_users_today <- new_users_predicted %>%
            filter(date == dt) %>%
            pull(predicted) %>%
            as.integer()
        new_dau[5] <- new_users_today
        dau_pred <- append(dau_pred, list(new_dau))
    }

    df <- data.frame(do.call(rbind, dau_pred))
    colnames(df) <- rownames(M)
    df$date <- dates
    df$dau <- df$new + df$current + df$reactivated + df$resurrected
    df$wau <- df$dau + df$at_risk_wau
    df$mau <- df$dau + df$at_risk_wau + df$at_risk_mau

    return(tibble(df))
}

# %%
