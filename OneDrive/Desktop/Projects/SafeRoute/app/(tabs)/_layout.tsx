import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { DarkTheme, DefaultTheme, ThemeProvider, NavigationContainer } from '@react-navigation/native';
import { useColorScheme } from '@/hooks/useColorScheme';
import HomeScreen from './index'; 
import CreateRoute from './CreateRoute';
import { RootStackParamList } from '../types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
      <NavigationContainer independent={true}>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen name="CreateRoute" component={CreateRoute} />
        </Stack.Navigator>
      </NavigationContainer>
  );
}