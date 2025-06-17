import { useQuery } from '@tanstack/react-query';
import { api } from '../config/api';
import { Employee } from '../types/employee';

const fetchEmployees = async (): Promise<Employee[]> => {
  const { data } = await api.get<Employee[]>('/api/employees');
  return data;
};

export const useEmployees = () => {
  return useQuery({
    queryKey: ['employees'],
    queryFn: fetchEmployees,
  });
}; 