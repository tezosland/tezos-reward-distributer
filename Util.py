def payment_file_name(pymnt_dir, pymnt_cycle, pymnt_addr, pymnt_type):
    return payment_dir_c(pymnt_dir, pymnt_cycle) + "/" + pymnt_addr + '_' + pymnt_type + '.txt'


def payment_dir_c(pymnt_dir, pymnt_cycle):
    return pymnt_dir + "/" + str(pymnt_cycle)
